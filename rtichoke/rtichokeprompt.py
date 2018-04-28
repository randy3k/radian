import os
import sys
from prompt_toolkit.application.current import get_app
from prompt_toolkit.completion import DynamicCompleter
from prompt_toolkit.lexers import DynamicLexer, PygmentsLexer
from prompt_toolkit.utils import is_windows

from pygments.lexers.r import SLexer
from .modalprompt import ModalPrompt
from .modalhistory import ModalInMemoryHistory, ModalFileHistory
from . import shell_cmd
from .keybinding import create_keybindings
from .completion import RCompleter, SmartPathCompleter


if not is_windows():
    from prompt_toolkit.input.vt100 import Vt100Input

    class CustomVt100Input(Vt100Input):
        @property
        def responds_to_cpr(self):
            return False


def create_rtichoke_prompt(options, history_file, inputhook):

    def get_lexer():
        if mp.prompt_mode in ["r", "browse"]:
            return PygmentsLexer(SLexer)
        return None

    def get_completer():
        if mp.prompt_mode in ["r", "browse"]:
            return RCompleter(timeout=mp.completion_timeout)
        elif mp.prompt_mode == "shell":
            return SmartPathCompleter()
        return None

    if options.no_history:
        history = ModalInMemoryHistory()
    elif not options.global_history and os.path.exists(history_file):
        history = ModalFileHistory(os.path.abspath(history_file))
    else:
        history = ModalFileHistory(os.path.join(os.path.expanduser("~"), history_file))

    def accept(buff):
        buff.last_working_index = buff.working_index
        app = get_app()

        if mp.prompt_mode == "browse":
            if buff.text.strip() in ["n", "s", "f", "c", "cont", "Q", "where", "help"]:
                mp.add_history = False

        if mp.prompt_mode in ["r", "browse", "readline"]:
            app.exit(result=buff.document.text)
            app.pre_run_callables.append(buff.reset)

        elif mp.prompt_mode in ["shell"]:
            # buffer will be reset to empty, we need to append history at this time point.
            mp.add_history = True
            buff.append_to_history()
            if mp.insert_new_line:
                sys.stdout.write("\n")
            shell_cmd.run_shell_command(buff.text)
            buff.reset()

    mp = ModalPrompt(
        lexer=DynamicLexer(get_lexer),
        completer=DynamicCompleter(get_completer),
        history=history,
        extra_key_bindings=create_keybindings(),
        tempfile_suffix=".R",
        accept=accept,
        input=CustomVt100Input(sys.stdin) if not is_windows() else None,
        inputhook=inputhook
    )

    # r mode message is set by RtichokeApplication.app_initialize()
    mp.prompt_mode = "r"
    mp.top_level_modes = ["r", "shell"]

    mp.auto_width = False
    mp.add_history = False

    return mp
