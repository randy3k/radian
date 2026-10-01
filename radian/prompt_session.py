import os
import re
import sys
import time

from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.enums import EditingMode
from prompt_toolkit.formatted_text import ANSI
from prompt_toolkit.layout.processors import HighlightMatchingBracketProcessor
from prompt_toolkit.lexers import PygmentsLexer
from prompt_toolkit.styles import style_from_pygments_cls
from prompt_toolkit.utils import get_term_environment_variable, is_windows
from pygments.styles import get_style_by_name
from rchitect.interface import (
    parse_text_complete,
    peek_event,
    polled_events,
    process_events,
    setoption,
)

from . import shell
from .completion import RCompleter, SmartPathCompleter
from .console import CustomInput, CustomOutput
from .key_bindings import (
    create_key_bindings,
    create_r_key_bindings,
    create_shell_key_bindings,
)
from .lexer import CustomSLexer as SLexer
from .lineedit import ModalFileHistory, ModalInMemoryHistory, ModalPromptSession


BROWSE_PATTERN = re.compile(r"Browse\[([0-9]+)\]> $")
BROWSE_COMMANDS = {"n", "s", "f", "c", "cont", "Q", "where", "help"}


# =============================================================================
# 1. History & InputHook Setup
# =============================================================================


def _create_history(options, settings):
    local_history_file = settings.local_history_file
    global_history_file = settings.global_history_file

    if options.no_history:
        return ModalInMemoryHistory()
    if not options.global_history and os.path.exists(local_history_file):
        return ModalFileHistory(
            os.path.abspath(local_history_file), settings.history_size
        )

    history_file = os.path.expandvars(os.path.expanduser(global_history_file))
    history_file_dir = os.path.dirname(history_file)
    if not os.path.exists(history_file_dir):
        os.makedirs(history_file_dir, 0o700)
    return ModalFileHistory(history_file, settings.history_size)


def _create_inputhook(get_session):
    if "RADIAN_NO_INPUTHOOK" in os.environ:
        return None

    terminal_width = [None]

    def inputhook(context):
        session = get_session()
        output_width = session.app.output.get_size().columns
        if output_width and terminal_width[0] != output_width:
            terminal_width[0] = output_width
            setoption("width", max(terminal_width[0], 20))

        while True:
            if context.input_is_ready():
                break
            try:
                if peek_event():
                    with session.app.input.detach():
                        with session.app.input.rare_mode():
                            process_events()
                else:
                    polled_events()
            except Exception:
                pass
            time.sleep(1.0 / 30)

    return inputhook


# =============================================================================
# 2. Mode Registration & Session Factory
# =============================================================================


def _register_modes(session, settings):
    input_processors = []
    if settings.highlight_matching_bracket:
        input_processors.append(HighlightMatchingBracketProcessor())

    r_completer = RCompleter(timeout=settings.completion_timeout)
    r_lexer = PygmentsLexer(SLexer)

    session.register_mode(
        name="r",
        prompt_message=lambda x: x,
        is_activated=lambda s: s._prompt_message == settings.prompt,
        history_book="r",
        insert_new_line=True,
        multiline=settings.indent_lines,
        completer=r_completer,
        complete_while_typing=settings.complete_while_typing,
        lexer=r_lexer,
        tempfile_suffix=".R",
        input_processors=input_processors,
        key_bindings=create_key_bindings(),
        prompt_key_bindings=create_r_key_bindings(session, parse_text_complete),
    )

    browse_level = [""]

    def browse_activator(s):
        m = BROWSE_PATTERN.match(s._prompt_message)
        if m:
            browse_level[0] = m.group(1)
            return True
        return False

    session.register_mode(
        name="browse",
        is_activated=browse_activator,
        prompt_message=lambda _: settings.browse_prompt.format(browse_level[0]),
        history_book="r",
        insert_new_line=True,
        multiline=settings.indent_lines,
        completer=r_completer,
        complete_while_typing=settings.complete_while_typing,
        keep_history=lambda text: not (
            settings.history_ignore_browser_commands and text.strip() in BROWSE_COMMANDS
        ),
        lexer=r_lexer,
        tempfile_suffix=".R",
        input_processors=input_processors,
        prompt_key_bindings=create_r_key_bindings(session, parse_text_complete),
    )

    def shell_process_text(s):
        text = s.default_buffer.text
        if text.strip():
            shell.run_command(text)

    session.register_mode(
        name="shell",
        prompt_message=lambda _: settings.shell_prompt,
        callback=shell_process_text,
        sticky=True,
        sticky_on_sigint=False,
        insert_new_line=True,
        multiline=settings.indent_lines,
        completer=SmartPathCompleter(),
        complete_while_typing=settings.complete_while_typing,
        lexer=None,
        input_processors=input_processors,
        prompt_key_bindings=create_shell_key_bindings(session),
    )

    session.register_mode(
        "unknown",
        prompt_message=lambda x: x,
        insert_new_line=False,
        complete_while_typing=False,
        keep_history=False,
        lexer=None,
        completer=None,
        prompt_key_bindings=None,
        input_processors=[],
    )


def create_radian_prompt_session(options, settings):
    history = _create_history(options, settings)
    output = (
        None
        if is_windows()
        else CustomOutput.from_pty(sys.stdout, term=get_term_environment_variable())
    )
    editing_mode = (
        EditingMode.VI if settings.editing_mode in ["vim", "vi"] else EditingMode.EMACS
    )

    session_ref = [None]

    def vi_mode_prompt():
        session = session_ref[0]
        if session.editing_mode == EditingMode.VI and settings.show_vi_mode_prompt:
            im = session.app.vi_state.input_mode.value
            vmp = settings.vi_mode_prompt
            if isinstance(vmp, str):
                return vmp.format(str(im)[3:6])
            return vmp[str(im)[3:6]]
        return ""

    def message():
        session = session_ref[0]
        if session.current_mode.prompt_message:
            return ANSI(
                vi_mode_prompt()
                + session.current_mode.prompt_message(session._prompt_message)
            )
        return session._prompt_message

    session = ModalPromptSession(
        message=message,
        style=style_from_pygments_cls(get_style_by_name(settings.color_scheme)),
        editing_mode=editing_mode,
        history=history,
        enable_history_search=True,
        search_no_duplicates=settings.history_search_no_duplicates,
        search_ignore_case=settings.history_search_ignore_case,
        enable_suspend=True,
        input=CustomInput(sys.stdin),
        output=output,
        auto_suggest=AutoSuggestFromHistory() if settings.auto_suggest else None,
        inputhook=_create_inputhook(lambda: session_ref[0]),
    )
    session_ref[0] = session

    _register_modes(session, settings)

    return session
