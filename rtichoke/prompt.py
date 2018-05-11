import os
import sys
import time
import errno

from lineedit import Mode, ModalPromptSession, ModalInMemoryHistory, ModalFileHistory
from prompt_toolkit.application.current import get_app
from prompt_toolkit.enums import EditingMode
from prompt_toolkit.formatted_text import ANSI
from prompt_toolkit.lexers import PygmentsLexer
from prompt_toolkit.output import ColorDepth
from prompt_toolkit.styles import style_from_pygments_cls
from prompt_toolkit.utils import is_windows, get_term_environment_variable

from pygments.styles import get_style_by_name
from pygments.lexers.r import SLexer

from rapi import reval, rexec, interface

from .keybindings import create_r_ish_keybindings, create_shell_keybindings, \
    create_readline_keybindings, create_keybindings
from .completion import RCompleter, SmartPathCompleter


PROMPT = "\x1b[34mr$>\x1b[0m "
SHELL_PROMPT = "\x1b[31m#!>\x1b[0m "
BROWSE_PROMPT = "\x1b[33mBrowse[{}]>\x1b[0m "


RETICULATE_MESSAGE = """
The host python environment is {}
and `rtichoke` is forcing `reticulate` to use this version of python.
Any python packages needed, e.g., `tensorflow` and `keras`,
have to be available to the current python environment.

File an issue at https://github.com/randy3k/rtichoke if you encounter any
difficulties in loading `reticulate`.
""".format(sys.executable).strip()


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


def intialize_modes(session):
    rmode = Mode(
        "r",
        message=lambda: ANSI(session.default_prompt),
        multiline=True,
        complete_while_typing=True,
        lexer=PygmentsLexer(SLexer),
        completer=RCompleter(timeout=session.completion_timeout),
        key_bindings=create_keybindings(),
        prompt_key_bindings=create_r_ish_keybindings()
    )

    shellmode = Mode(
        "shell",
        message=ANSI(session.shell_prompt),
        multiline=True,
        complete_while_typing=False,
        completer=SmartPathCompleter(),
        prompt_key_bindings=create_shell_keybindings()
    )

    browsemode = Mode(
        "browse",
        message=lambda: ANSI(session.browse_prompt.format(session.browse_level)),
        multiline=True,
        complete_while_typing=True,
        lexer=PygmentsLexer(SLexer),
        completer=RCompleter(timeout=session.completion_timeout),
        prompt_key_bindings=create_r_ish_keybindings(),
        switchable_from=False,
        switchable_to=False
    )

    readlinemode = Mode(
        "readline",
        message=lambda: ANSI(session.readline_prompt),
        multiline=False,
        prompt_key_bindings=create_readline_keybindings(),
        switchable_from=False,
        switchable_to=False
    )

    session.register_mode(rmode)
    session.register_mode(shellmode)
    session.register_mode(browsemode)
    session.register_mode(readlinemode)


def reticulate_set_message(message):
    reval("""
    setHook(packageEvent("reticulate", "onLoad"),
            function(...) packageStartupMessage("{}"))
    """.format(message.replace('\\', '\\\\').replace('"', '\\"')))


def session_initialize(session):
    if not interface.get_option("rtichoke.suppress_reticulate_message", False):
        reticulate_set_message(RETICULATE_MESSAGE)

    if interface.get_option("rtichoke.editing_mode", "emacs") in ["vim", "vi"]:
        session.app.editing_mode = EditingMode.VI
    else:
        session.app.editing_mode = EditingMode.EMACS

    color_scheme = interface.get_option("rtichoke.color_scheme", "native")
    session.style = style_from_pygments_cls(get_style_by_name(color_scheme))

    session.auto_match = interface.get_option("rtichoke.auto_match", False)
    session.auto_indentation = interface.get_option("rtichoke.auto_indentation", True)
    session.tab_size = int(interface.get_option("rtichoke.tab_size", 4))
    session.complete_while_typing = interface.get_option("rtichoke.complete_while_typing", True)
    session.completion_timeout = interface.get_option("rtichoke.completion_timeout", 0.05)

    session.history_search_no_duplicates = interface.get_option("rtichoke.history_search_no_duplicates", False)
    session.insert_new_line = interface.get_option("rtichoke.insert_new_line", True)

    prompt = interface.get_option("rtichoke.prompt", None)
    if not prompt:
        sys_prompt = interface.get_option("prompt")
        if sys_prompt == "> ":
            prompt = PROMPT
        else:
            prompt = sys_prompt

    session.default_prompt = prompt
    interface.set_option("prompt", prompt)

    shell_prompt = interface.get_option("rtichoke.shell_prompt", SHELL_PROMPT)
    session.shell_prompt = shell_prompt

    browse_prompt = interface.get_option("rtichoke.browse_prompt", BROWSE_PROMPT)
    session.browse_prompt = browse_prompt

    set_width_on_resize = interface.get_option("setWidthOnResize", True)
    session.auto_width = interface.get_option("rtichoke.auto_width", set_width_on_resize)
    output_width = session.app.output.get_size().columns
    if output_width and session.auto_width:
        interface.set_option("width", output_width)

    # necessary on windows
    interface.set_option("menu.graphics", False)

    # enables completion of installed package names
    if interface.rcopy(interface.reval("rc.settings('ipck')")) is None:
        interface.reval("rc.settings(ipck = TRUE)")


def create_rtichoke_prompt_session(options, history_file):

    if options.no_history:
        history = ModalInMemoryHistory()
    elif not options.global_history and os.path.exists(history_file):
        history = ModalFileHistory(os.path.abspath(history_file))
    else:
        history = ModalFileHistory(os.path.join(os.path.expanduser("~"), history_file))

    def before_accept(buff):
        if session.current_mode_name == "browse":
            if buff.text.strip() in ["n", "s", "f", "c", "cont", "Q", "where", "help"]:
                session.add_history = False

    if is_windows():
        output = None
    else:
        output = CustomVt100Output.from_pty(sys.stdout, term=get_term_environment_variable())

    def get_inputhook():
        terminal_width = [None]

        def _(context):
            while True:
                if context.input_is_ready():
                    break
                rexec(interface.process_events)

                output_width = session.app.output.get_size().columns
                if output_width and terminal_width[0] != output_width:
                    terminal_width[0] = output_width
                    interface.set_option("width", max(terminal_width[0], 20))
                time.sleep(1.0 / 30)

        return _

    session = ModalPromptSession(
        color_depth=ColorDepth.default(term=os.environ.get("TERM")),
        history=history,
        tempfile_suffix=".R",
        input=CustomVt100Input(sys.stdin) if not is_windows() else None,
        output=output,
        inputhook=get_inputhook(),
        before_accept=before_accept
    )

    return session
