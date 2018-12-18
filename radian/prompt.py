from __future__ import unicode_literals

import os
import re
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

from rchitect import rcall, rcopy, reval
from rchitect.interface import roption, setoption, process_events
from rchitect.namespace import new_env, set_hook, package_event

from .keybindings import create_r_keybindings, create_shell_keybindings, create_keybindings
from .completion import RCompleter, SmartPathCompleter


PROMPT = "\x1b[34mr$>\x1b[0m "
SHELL_PROMPT = "\x1b[31m#!>\x1b[0m "
BROWSE_PROMPT = "\x1b[33mBrowse[{}]>\x1b[0m "
BROWSE_PATTERN = re.compile(r"Browse\[([0-9]+)\]> $")


RETICULATE_MESSAGE = """
The host python environment is {}
and `radian` is forcing `reticulate` to use this version of python.
Any python packages needed, e.g., `tensorflow` and `keras`,
have to be available to the current python environment.

File an issue at https://github.com/randy3k/radian if you encounter any
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


class RadianMode(Mode):
    def __init__(
            self,
            name,
            native,
            on_done=None,
            activator=None,
            return_result=None,
            insert_new_line=False,
            **kwargs):

        self.native = native
        if native:
            assert on_done is None
        else:
            assert on_done is not None
        self.on_done = on_done
        self.activator = activator
        self.return_result = return_result
        self.insert_new_line = insert_new_line
        super(RadianMode, self).__init__(name, **kwargs)


def intialize_modes(session):
    from ctypes import c_int
    from rchitect.interface import rexec_p, rstring_p
    from rchitect.internals import Rf_protect, Rf_unprotect, R_ParseVector, R_NilValue
    from .shell import run_command

    def browse_activator(session):
        message = session.prompt_text
        if BROWSE_PATTERN.match(message):
            session.browse_level = BROWSE_PATTERN.match(message).group(1)
            return True
        else:
            return False

    def browse_on_pre_accept(session):
        if session.default_buffer.text.strip() in [
                "n", "s", "f", "c", "cont", "Q", "where", "help"]:
            session.add_history = False

    def shell_process_text(session):
        text = session.default_buffer.text
        run_command(text)

    def prase_text_complete(text):
        status = c_int()
        s = Rf_protect(rstring_p(text))
        try:
            orig_stderr = sys.stderr
            sys.stderr = None
            rexec_p(R_ParseVector, s, -1, status, R_NilValue)
        except Exception:
            return True
        finally:
            sys.stderr = orig_stderr
            Rf_unprotect(1)
        return status.value != 2

    def enable_reticulate_prompt():
        enable = "reticulate" in rcopy(reval("rownames(installed.packages())")) and \
                roption("radian.enable_reticulate_prompt", True)
        if enable:
            setoption("radian.suppress_reticulate_message", True)
        return enable

    session.register_mode(
        "r",
        native=True,
        activator=lambda session: session.prompt_text == session.default_prompt,
        insert_new_line=True,
        history_share_with="browse",
        message=ANSI(session.default_prompt),
        multiline=session.indent_lines,
        complete_while_typing=session.complete_while_typing,
        lexer=PygmentsLexer(SLexer),
        completer=RCompleter(timeout=session.completion_timeout),
        key_bindings=create_keybindings(),
        prompt_key_bindings=create_r_keybindings(prase_text_complete, enable_reticulate_prompt)
    )
    session.register_mode(
        "shell",
        native=False,
        on_done=shell_process_text,
        insert_new_line=True,
        message=ANSI(session.shell_prompt),
        multiline=session.indent_lines,
        complete_while_typing=session.complete_while_typing,
        lexer=None,
        completer=SmartPathCompleter(),
        prompt_key_bindings=create_shell_keybindings()
    )
    session.register_mode(
        "browse",
        native=True,
        activator=browse_activator,
        insert_new_line=True,
        history_share_with="r",
        message=lambda: ANSI(session.browse_prompt.format(session.browse_level)),
        multiline=session.indent_lines,
        complete_while_typing=True,
        lexer=PygmentsLexer(SLexer),
        completer=RCompleter(timeout=session.completion_timeout),
        prompt_key_bindings=create_r_keybindings(prase_text_complete, enable_reticulate_prompt),
        switchable_from=False,
        switchable_to=False
    )
    session.register_mode(
        "unknown",
        native=True,
        insert_new_line=False,
        message=lambda: ANSI(session.prompt_text),
        complete_while_typing=False,
        lexer=None,
        completer=None,
        prompt_key_bindings=None,
        switchable_from=False,
        switchable_to=False
    )


def session_initialize(session):
    if not roption("radian.suppress_reticulate_message", False):
        def reticulate_hook(*args):
            if not roption("radian.suppress_reticulate_message", False):
                rcall("packageStartupMessage", RETICULATE_MESSAGE)

        set_hook(package_event("reticulate", "onLoad"), reticulate_hook)

    if roption("radian.enable_reticulate_prompt", True):
        def reticulate_prompt(*args):
            rcall(
                ("base", "source"),
                os.path.join(os.path.dirname(__file__), "data", "register_reticulate.R"),
                new_env())

        set_hook(package_event("reticulate", "onLoad"), reticulate_prompt)

    if roption("radian.editing_mode", "emacs") in ["vim", "vi"]:
        session.app.editing_mode = EditingMode.VI
    else:
        session.app.editing_mode = EditingMode.EMACS

    color_scheme = roption("radian.color_scheme", "native")
    session.style = style_from_pygments_cls(get_style_by_name(color_scheme))

    session.auto_match = roption("radian.auto_match", False)
    session.auto_indentation = roption("radian.auto_indentation", True)
    session.tab_size = int(roption("radian.tab_size", 4))
    session.complete_while_typing = roption("radian.complete_while_typing", True)
    session.completion_timeout = roption("radian.completion_timeout", 0.05)

    session.history_search_no_duplicates = roption("radian.history_search_no_duplicates", False)
    session.insert_new_line = roption("radian.insert_new_line", True)
    session.indent_lines = roption("radian.indent_lines", True)

    prompt = roption("radian.prompt", None)
    if not prompt:
        sys_prompt = roption("prompt")
        if sys_prompt == "> ":
            prompt = PROMPT
        else:
            prompt = sys_prompt

    session.default_prompt = prompt
    setoption("prompt", prompt)

    shell_prompt = roption("radian.shell_prompt", SHELL_PROMPT)
    session.shell_prompt = shell_prompt

    browse_prompt = roption("radian.browse_prompt", BROWSE_PROMPT)
    session.browse_prompt = browse_prompt

    set_width_on_resize = roption("setWidthOnResize", True)
    session.auto_width = roption("radian.auto_width", set_width_on_resize)
    output_width = session.app.output.get_size().columns
    if output_width and session.auto_width:
        setoption("width", output_width)

    # necessary on windows
    setoption("menu.graphics", False)

    # enables completion of installed package names
    if rcopy(reval("rc.settings('ipck')")) is None:
        reval("rc.settings(ipck = TRUE)")

    # backup the updated settings
    session._backup_settings()


def create_radian_prompt_session(options, history_file):

    if options.no_history:
        history = ModalInMemoryHistory()
    elif not options.global_history and os.path.exists(history_file):
        history = ModalFileHistory(os.path.abspath(history_file))
    else:
        history = ModalFileHistory(os.path.join(os.path.expanduser("~"), history_file))

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
                try:
                    process_events()
                except Exception:
                    pass

                output_width = session.app.output.get_size().columns
                if output_width and terminal_width[0] != output_width:
                    terminal_width[0] = output_width
                    setoption("width", max(terminal_width[0], 20))
                time.sleep(1.0 / 30)

        return _

    session = ModalPromptSession(
        color_depth=ColorDepth.default(term=os.environ.get("TERM")),
        history=history,
        enable_history_search=True,
        enable_suspend=True,
        tempfile_suffix=".R",
        input=CustomVt100Input(sys.stdin) if not is_windows() else None,
        output=output,
        inputhook=get_inputhook(),
        mode_class=RadianMode
    )

    return session
