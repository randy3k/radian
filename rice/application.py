from __future__ import unicode_literals
import sys
import os
import time
import subprocess
import shlex

from .session import RSession
from . import interface
from . import api
from . import callbacks
from prompt_toolkit import Prompt
from prompt_toolkit.eventloop import create_event_loop, set_event_loop, run_in_executor
from prompt_toolkit.application.current import get_app

from prompt_toolkit.utils import is_windows
from prompt_toolkit.layout.lexers import PygmentsLexer, DynamicLexer
from pygments.lexers.r import SLexer
from prompt_toolkit.styles import default_style, merge_styles, style_from_pygments
from pygments.styles import get_style_by_name
from prompt_toolkit.history import FileHistory
from prompt_toolkit.layout.processors import HighlightMatchingBracketProcessor

from prompt_toolkit.enums import EditingMode
from prompt_toolkit.formatted_text import ANSI

from .completion import MultiPromptCompleter
from .keybinding import create_keybindings


PROMPT = "r$> "
COLORED_PROMPT = "\x1b[34m" + PROMPT.strip() + "\x1b[0m "


class MultiPrompt(Prompt):
    _message = {
        "r": PROMPT,
        "help": "\x1b[33m?$>\x1b[0m ",
        "help_search": "\x1b[33m??>\x1b[0m ",
        "shell": "\x1b[31m!%>\x1b[0m "
    }
    prompt_mode = "r"

    def __init__(self, *args, **kwargs):
        super(MultiPrompt, self).__init__(*args, **kwargs)
        self.prompt_mode = "r"
        self.app.mp = self

    def set_prompt_mode_message(self, mode, message):
        self._message[mode] = message

    def prompt_mode_message(self, mode, colorized=False):
        message = self._message[mode]
        if colorized and message == PROMPT:
            message = COLORED_PROMPT
        return message

    def set_prompt_mode(self, mode):
        self.prompt_mode = mode
        self.message = ANSI(self.prompt_mode_message(mode, colorized=True))

    def readconsole(self, **kwargs):
        message = self.prompt_mode_message(self.prompt_mode, colorized=True)
        return self.prompt(ANSI(message), **kwargs)

    def readline(self, message):
        return self.prompt(
            message=message,
            multiline=False,
            complete_while_typing=False,
            lexer=None,
            completer=None,
            history=None,
            extra_key_bindings=None)

    def run_shell_command(self, command):

        def run_command():
            if not command:
                sys.stdout.write("\n")
                return

            scommand = shlex.split(command, posix=not sys.platform.startswith('win'))
            if scommand[0] == "cd":
                if len(scommand) != 2:
                    sys.stdout.write("cd method only takes one argument\n\n")
                    return
                try:
                    path = scommand[1]
                    path = os.path.expanduser(path)
                    path = os.path.expandvars(path)
                    os.chdir(path)
                except Exception as e:
                    print(e)
                finally:
                    sys.stdout.write(os.getcwd())
                    sys.stdout.write("\n")

            else:
                if is_windows():
                    p = subprocess.Popen(command, shell=True, stdin=sys.stdin, stdout=sys.stdout)
                else:
                    shell = os.path.basename(os.environ.get("SHELL", "/bin/sh"))
                    p = subprocess.Popen([shell, "-c", command], stdin=sys.stdin, stdout=sys.stdout)

                p.wait()
            sys.stdout.write("\n")

        return self.app.run_coroutine_in_terminal(lambda: run_in_executor(run_command))


if not is_windows():
    from prompt_toolkit.input.vt100 import Vt100Input

    class CustomVt100Input(Vt100Input):
        @property
        def responds_to_cpr(self):
            return False


def create_multi_prompt():

    history = FileHistory(os.path.join(os.path.expanduser("~"), ".rice_history"))
    if not is_windows():
        vt100 = CustomVt100Input(sys.stdin)

    def process_events(context):
        while True:
            if context.input_is_ready():
                break
            api.process_events()
            time.sleep(1.0 / 30)

    set_event_loop(create_event_loop(inputhook=process_events))

    def get_lexer():
        app = get_app(return_none=False)
        if hasattr(app, "mp"):
            if app.mp.prompt_mode in ["r", "help", "help_search"]:
                return PygmentsLexer(SLexer)
        return None

    mp = MultiPrompt(
        multiline=True,
        complete_while_typing=True,
        enable_suspend=True,
        lexer=DynamicLexer(get_lexer),
        completer=MultiPromptCompleter(),
        history=history,
        extra_key_bindings=create_keybindings(),
        extra_input_processor=HighlightMatchingBracketProcessor(),
        input=vt100 if not is_windows() else None
    )

    def on_render(app):
        if app.is_aborting:
            sys.stdout.write("\n")

    mp.app.on_render += on_render

    return mp


class RiceApplication(object):
    initialized = False

    def app_initialize(self, mp):
        if is_windows():
            cp = api.localecp()
            if cp and cp.value:
                api.ENCODING = "cp" + str(cp.value)

        if interface.get_option("rice.editing_mode", "emacs") in ["vim", "vi"]:
            mp.app.editing_mode = EditingMode.VI
        else:
            mp.app.editing_mode = EditingMode.EMACS

        color_scheme = interface.get_option("rice.color_scheme", "native")
        self.style = merge_styles([
            default_style(),
            style_from_pygments(get_style_by_name(color_scheme))])

        mp.app.auto_indentation = interface.get_option("rice.auto_indentation", 1) == 1

        prompt = interface.get_option("rice.prompt", None)
        if not prompt:
            sys_prompt = interface.get_option("prompt")
            if sys_prompt == "> ":
                prompt = PROMPT
            else:
                prompt = sys_prompt

        interface.set_option("prompt", prompt)
        mp.set_prompt_mode_message("r", prompt)

        # print welcome message
        sys.stdout.write(interface.r_version())

    def run(self):
        mp = create_multi_prompt()

        def result_from_prompt(message):
            if not self.initialized:
                self.app_initialize(mp)
                message = mp.prompt_mode_message("r")
                self.initialized = True

            sys.stdout.write("\n")
            text = None
            while text is None:
                try:
                    if message == mp.prompt_mode_message("r"):
                        text = mp.readconsole(style=self.style)
                    else:
                        # invoked by `readline`
                        text = mp.readline(message)

                except Exception as e:
                    if isinstance(e, EOFError):
                        # todo: confirmation
                        return None
                    else:
                        raise e
                except KeyboardInterrupt:
                    pass

            return text

        rsession = RSession()
        rsession.read_console = callbacks.create_read_console(result_from_prompt)
        rsession.write_console_ex = callbacks.write_console_ex
        rsession.clean_up = callbacks.clean_up
        rsession.show_message = callbacks.show_message

        # to make api work
        api.rsession = rsession

        rsession.run()
