import os
import sys
import errno

from prompt_toolkit.application.current import get_app
from prompt_toolkit.completion import DynamicCompleter
from prompt_toolkit.lexers import DynamicLexer, PygmentsLexer
from prompt_toolkit.output import ColorDepth
from prompt_toolkit.utils import is_windows, get_term_environment_variable

from pygments.lexers.r import SLexer

from .modalprompt import ModalPrompt
from .modalhistory import ModalInMemoryHistory, ModalFileHistory
from . import shell_cmd
from .keybinding import create_keybindings
from .completion import RCompleter, SmartPathCompleter


if not is_windows():
    from prompt_toolkit.input.vt100 import Vt100Input
    from prompt_toolkit.output.vt100 import Vt100_Output

    class CustomVt100Input(Vt100Input):
        @property
        def responds_to_cpr(self):
            return False

    class CustomVt100Output(Vt100_Output):

        def flush(self):
            # it is needed when the stdout was redirected
            # see https://github.com/Non-Contradiction/JuliaCall/issues/39
            try:
                if self._buffer:
                    data = ''.join(self._buffer)
                    if self.write_binary:
                        if hasattr(self.stdout, 'buffer'):
                            out = self.stdout.buffer  # Py3.
                        else:
                            out = self.stdout
                        out.write(data.encode(self.stdout.encoding or 'utf-8', 'replace'))
                    else:
                        self.stdout.write(data)
                    self._buffer = []
            except IOError as e:
                if e.args and e.args[0] == errno.EINTR:
                    pass
                elif e.args and e.args[0] == 0:
                    pass
                else:
                    raise
            try:
                self.stdout.flush()
            except IOError as e:
                if e.args and e.args[0] == errno.EAGAIN:
                    app = get_app()
                    app.renderer.render(app, app.layout)
                    pass
                else:
                    raise


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

    if is_windows():
        output = None
    else:
        output = CustomVt100Output.from_pty(sys.stdout, term=get_term_environment_variable())

    mp = ModalPrompt(
        lexer=DynamicLexer(get_lexer),
        completer=DynamicCompleter(get_completer),
        color_depth=ColorDepth.default(term=os.environ.get("TERM")),
        history=history,
        extra_key_bindings=create_keybindings(),
        tempfile_suffix=".R",
        accept=accept,
        input=CustomVt100Input(sys.stdin) if not is_windows() else None,
        output=output,
        inputhook=inputhook
    )

    # r mode message is set by RtichokeApplication.app_initialize()
    mp.prompt_mode = "r"
    mp.top_level_modes = ["r", "shell"]

    mp.auto_width = False
    mp.add_history = False

    return mp
