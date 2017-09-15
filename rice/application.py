from __future__ import unicode_literals
import sys
import os
import time

from .instance import Rinstance
from . import interface
from . import api
from . import callbacks
from prompt_toolkit import Prompt
from prompt_toolkit.eventloop import create_event_loop, set_event_loop

from prompt_toolkit.utils import is_windows
from prompt_toolkit.layout.lexers import PygmentsLexer
from pygments.lexers.r import SLexer
from prompt_toolkit.styles import default_style, merge_styles, style_from_pygments
from pygments.styles import get_style_by_name
from prompt_toolkit.history import FileHistory
from prompt_toolkit.layout.processors import HighlightMatchingBracketProcessor

from prompt_toolkit.enums import EditingMode
from prompt_toolkit.formatted_text import ANSI

from .completion import RCompleter
from .keybinding import create_keybindings


PROMPT = "r$> "
COLORED_PROMPT = "\x1b[34m" + PROMPT.strip() + "\x1b[0m "


class MultiPrompt(Prompt):
    _message = {
        "r": PROMPT,
        "help": "\x1b[33mhelp?>\x1b[0m ",
        "help_search": "\x1b[33mhelp??>\x1b[0m ",
        "debug": "debug%> "
    }

    def __init__(self, *args, **kwargs):
        super(MultiPrompt, self).__init__(*args, **kwargs)
        self.app.prompt_mode = "r"

    def set_prompt_message(self, mode, message):
        self._message[mode] = message

    def prompt_message(self, mode):
        return self._message[mode]

    def readconsole(self, **kwargs):
        message = self.prompt_message(self.app.prompt_mode)
        if message == PROMPT:
            message = COLORED_PROMPT
        message = ANSI(message)

        return super(MultiPrompt, self).prompt(message, **kwargs)

    def readline(self, message):
        return super(MultiPrompt, self).prompt(
            message=message,
            multiline=False,
            complete_while_typing=False,
            lexer=None,
            completer=None,
            history=None,
            extra_key_bindings=None)


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

    rcompleter = RCompleter()

    mp = MultiPrompt(
        multiline=True,
        complete_while_typing=True,
        enable_suspend=True,
        lexer=PygmentsLexer(SLexer),
        completer=rcompleter,
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
        mp.set_prompt_message("r", prompt)

        # print welcome message
        sys.stdout.write(interface.r_version())

    def run(self):
        mp = create_multi_prompt()

        def result_from_prompt(message):
            if not self.initialized:
                self.app_initialize(mp)
                message = mp.prompt_message("r")
                self.initialized = True

            sys.stdout.write("\n")
            text = None
            while text is None:
                try:
                    if message == mp.prompt_message("r"):
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

        rinstance = Rinstance()
        rinstance.read_console = callbacks.create_read_console(result_from_prompt)
        rinstance.write_console_ex = callbacks.write_console_ex
        rinstance.clean_up = callbacks.clean_up
        rinstance.show_message = callbacks.show_message

        # to make api work
        api.rinstance = rinstance

        rinstance.run()
