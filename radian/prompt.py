from __future__ import unicode_literals

import os
import re
import sys
import time

from lineedit import Mode, ModalPromptSession, ModalInMemoryHistory, ModalFileHistory
from prompt_toolkit.formatted_text import ANSI
from prompt_toolkit.lexers import PygmentsLexer
from prompt_toolkit.output import ColorDepth
from prompt_toolkit.utils import is_windows, get_term_environment_variable

from pygments.lexers.r import SLexer

from rchitect._libR import ffi, lib
from rchitect import rcopy, reval
from rchitect.interface import rstring_p, roption, setoption, process_events
# from rchitect.namespace import new_env, set_hook, package_event

from .shell import run_command
from .keybindings import create_r_keybindings, create_shell_keybindings, create_keybindings
from .completion import RCompleter, SmartPathCompleter
from .vt100 import CustomVt100Input, CustomVt100Output


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


def register_modes(session):
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
        status = ffi.new("ParseStatus[1]")
        s = lib.Rf_protect(rstring_p(text))
        orig_stderr = sys.stderr
        sys.stderr = None
        lib.R_ParseVector(s, -1, status, lib.R_NilValue)
        sys.stderr = orig_stderr
        lib.Rf_unprotect(1)
        return status[0] != 2

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
