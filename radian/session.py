from __future__ import unicode_literals

import os
import re
import sys
import time

from lineedit import Mode, ModalPromptSession, ModalInMemoryHistory, ModalFileHistory
from prompt_toolkit.formatted_text import ANSI
from prompt_toolkit.layout.processors import HighlightMatchingBracketProcessor
from prompt_toolkit.lexers import PygmentsLexer
from prompt_toolkit.output import ColorDepth
from prompt_toolkit.styles import style_from_pygments_cls
from prompt_toolkit.utils import is_windows, get_term_environment_variable
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory

from pygments.styles import get_style_by_name

from rchitect import rcopy, rcall
from rchitect.interface import setoption, process_events, peek_event, polled_events

from six import string_types

from . import shell
from .rutils import prase_text_complete
from .key_bindings import create_r_key_bindings, create_shell_key_bindings, create_key_bindings
from .completion import RCompleter, SmartPathCompleter
from .io import CustomInput, CustomOutput
from .lexer import CustomSLexer as SLexer


PROMPT = "\x1b[34mr$>\x1b[0m "
SHELL_PROMPT = "\x1b[31m#!>\x1b[0m "
BROWSE_PROMPT = "\x1b[33mBrowse[{}]>\x1b[0m "
BROWSE_PATTERN = re.compile(r"Browse\[([0-9]+)\]> $")
VI_MODE_PROMPT = "\x1b[34m[{}]\x1b[0m "


class RadianMode(Mode):
    def __init__(
            self,
            name,
            activator=None,
            on_post_accept=None,
            insert_new_line=False,
            **kwargs):
        self.activator = activator
        self.on_post_accept = on_post_accept
        self.insert_new_line = insert_new_line
        super(RadianMode, self).__init__(name, **kwargs)


def apply_settings(session, settings):
    setoption("prompt", settings.prompt)

    if settings.auto_width:
        output_width = session.app.output.get_size().columns
        if output_width:
            setoption("width", output_width)

    # necessary on windows
    setoption("menu.graphics", False)

    def askpass(message):
        from prompt_toolkit import prompt
        return prompt(message, is_password=True)

    setoption("askpass", askpass)

    # enables completion of installed package names
    if rcopy(rcall(("utils", "rc.settings"), "ipck")) is None:
        rcall(("utils", "rc.settings"), ipck=True)


def create_radian_prompt_session(options, settings):

    local_history_file = settings.local_history_file
    global_history_file = settings.global_history_file
    if options.no_history:
        history = ModalInMemoryHistory()
    elif not options.global_history and os.path.exists(local_history_file):
        history = ModalFileHistory(os.path.abspath(local_history_file))
    else:
        history_file = os.path.join(os.path.expanduser(global_history_file))
        history_file = os.path.expandvars(history_file)
        history_file_dir = os.path.dirname(history_file)
        if not os.path.exists(history_file_dir):
            os.makedirs(history_file_dir, 0o700)
        history = ModalFileHistory(history_file)

    if is_windows():
        output = None
    else:
        output = CustomOutput.from_pty(sys.stdout, term=get_term_environment_variable())

    def get_inputhook():
        # make testing more robust
        if "RADIAN_NO_INPUTHOOK" in os.environ:
            return None

        terminal_width = [None]

        def _(context):
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

        return _

    def vi_mode_prompt():
        if session.editing_mode.lower() == "vi" and settings.show_vi_mode_prompt:
            im = session.app.vi_state.input_mode
            vi_mode_prompt = settings.vi_mode_prompt
            if isinstance(vi_mode_prompt, string_types):
                return vi_mode_prompt.format(str(im)[3:6])
            else:
                return vi_mode_prompt[str(im)[3:6]]
        return ""

    def message():
        if hasattr(session.current_mode, "get_message"):
            return ANSI(vi_mode_prompt() + session.current_mode.get_message())
        elif hasattr(session.current_mode, "message"):
            message = session.current_mode.message
            if callable(message):
                return ANSI(vi_mode_prompt() + message())
            else:
                return ANSI(vi_mode_prompt() + message)
        else:
            return ""

    session = ModalPromptSession(
        message=message,
        color_depth=ColorDepth.default(term=os.environ.get("TERM")),
        style=style_from_pygments_cls(get_style_by_name(settings.color_scheme)),
        editing_mode="VI" if settings.editing_mode in ["vim", "vi"] else "EMACS",
        history=history,
        enable_history_search=True,
        history_search_no_duplicates=settings.history_search_no_duplicates,
        search_ignore_case=settings.history_search_ignore_case,
        enable_suspend=True,
        tempfile_suffix=".R",
        input=CustomInput(sys.stdin),
        output=output,
        inputhook=get_inputhook(),
        mode_class=RadianMode,
        auto_suggest=AutoSuggestFromHistory() if settings.auto_suggest else None
    )

    apply_settings(session, settings)

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
        shell.run_command(text)

    input_processors = []
    if settings.highlight_matching_bracket:
        input_processors.append(HighlightMatchingBracketProcessor())

    session.register_mode(
        "r",
        activator=lambda session: session.prompt_text == settings.prompt,
        insert_new_line=True,
        history_share_with="browse",
        get_message=lambda: settings.prompt,
        multiline=settings.indent_lines,
        complete_while_typing=settings.complete_while_typing,
        lexer=PygmentsLexer(SLexer),
        completer=RCompleter(timeout=settings.completion_timeout),
        key_bindings=create_key_bindings(),
        input_processors=input_processors,
        prompt_key_bindings=create_r_key_bindings(prase_text_complete)
    )
    session.register_mode(
        "shell",
        on_post_accept=shell_process_text,
        insert_new_line=True,
        get_message=lambda: settings.shell_prompt,
        multiline=settings.indent_lines,
        complete_while_typing=settings.complete_while_typing,
        lexer=None,
        completer=SmartPathCompleter(),
        prompt_key_bindings=create_shell_key_bindings()
    )
    session.register_mode(
        "browse",
        activator=browse_activator,
        # on_pre_accept=browse_on_pre_accept,  # disable
        insert_new_line=True,
        history_share_with="r",
        get_message=lambda: settings.browse_prompt.format(session.browse_level),
        multiline=settings.indent_lines,
        complete_while_typing=True,
        lexer=PygmentsLexer(SLexer),
        completer=RCompleter(timeout=settings.completion_timeout),
        input_processors=input_processors,
        prompt_key_bindings=create_r_key_bindings(prase_text_complete),
        switchable_from=False,
        switchable_to=False
    )
    session.register_mode(
        "unknown",
        insert_new_line=False,
        get_message=lambda: session.prompt_text,
        complete_while_typing=False,
        lexer=None,
        completer=None,
        prompt_key_bindings=None,
        switchable_from=False,
        switchable_to=False,
        input_processors=[]
    )

    return session
