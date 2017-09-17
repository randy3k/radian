from __future__ import unicode_literals
import sys
import os
import time

from .session import RSession
from . import interface
from . import api
from . import callbacks
from .multiprompt import MultiPrompt

from prompt_toolkit.eventloop import create_event_loop, set_event_loop

from prompt_toolkit.utils import is_windows
from prompt_toolkit.layout.lexers import PygmentsLexer
from pygments.lexers.r import SLexer
from prompt_toolkit.styles import default_style, merge_styles, style_from_pygments
from pygments.styles import get_style_by_name
from prompt_toolkit.history import FileHistory
from prompt_toolkit.layout.processors import HighlightMatchingBracketProcessor

from prompt_toolkit.formatted_text import ANSI
from prompt_toolkit.enums import EditingMode

from .completion import MultiPromptCompleter
from .keybinding import create_keybindings


PROMPT = "r$> "
COLORED_PROMPT = "\x1b[34m" + PROMPT.strip() + "\x1b[0m "


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

    mp = MultiPrompt(
        multiline=True,
        complete_while_typing=True,
        enable_suspend=True,
        lexer=PygmentsLexer(SLexer),
        completer=MultiPromptCompleter(),
        history=history,
        extra_key_bindings=create_keybindings(),
        extra_input_processor=HighlightMatchingBracketProcessor(),
        input=vt100 if not is_windows() else None
    )

    # r mode message is set by RiceApplication.app_initialize()
    mp.prompt_mode = "r"
    mp.set_prompt_mode_message("shell", ANSI("\x1b[31m!%>\x1b[0m "))

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
        if prompt:
            mp.set_prompt_mode_message("r", ANSI(prompt))
        else:
            sys_prompt = interface.get_option("prompt")
            if sys_prompt == "> ":
                prompt = PROMPT
                mp.set_prompt_mode_message("r", ANSI(COLORED_PROMPT))
            else:
                prompt = sys_prompt
                mp.set_prompt_mode_message("r", ANSI(prompt))

        self.default_prompt = prompt
        interface.set_option("prompt", prompt)

        # print welcome message
        sys.stdout.write(interface.r_version())

    def run(self):
        mp = create_multi_prompt()

        def result_from_prompt(message):
            if not self.initialized:
                self.app_initialize(mp)
                message = self.default_prompt
                self.initialized = True

            sys.stdout.write("\n")
            text = None
            while text is None:
                try:
                    if message == self.default_prompt:
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
