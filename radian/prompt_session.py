import os
import re
import sys
import time

from .lineedit.prompt import ModalPromptSession, ModeSpec
from .lineedit.history import ModalInMemoryHistory, ModalFileHistory
from prompt_toolkit.enums import EditingMode
from prompt_toolkit.formatted_text import ANSI
from prompt_toolkit.layout.processors import HighlightMatchingBracketProcessor
from prompt_toolkit.lexers import PygmentsLexer
from prompt_toolkit.styles import style_from_pygments_cls
from prompt_toolkit.utils import is_windows, get_term_environment_variable
from prompt_toolkit.validation import Validator
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.eventloop.inputhook import set_eventloop_with_inputhook

from pygments.styles import get_style_by_name

from rchitect import rcopy, rcall, robject
from rchitect.interface import roption, setoption, process_events, peek_event, polled_events

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


class RadianModeSpec(ModeSpec):
    def __init__(
            self,
            name,
            prompt_message=None,
            is_activated=None,
            callback=None,
            sticky=False,
            sticky_on_sigint=False,
            insert_new_line=False,
            insert_new_line_on_sigint=False,
            **kwargs):
        self.prompt_message = prompt_message
        self.is_activated = is_activated
        self.callback = callback
        self.sticky = sticky
        self.sticky_on_sigint = sticky_on_sigint
        self.insert_new_line = insert_new_line
        self.insert_new_line_on_sigint = insert_new_line_on_sigint
        super().__init__(name, **kwargs)


class RadianPromptSession(ModalPromptSession):
    _spec_class = RadianModeSpec
    _prompt_message = ""

    def mode_to_be_activated(self):
        for name in reversed(self.specs):
            spec = self.specs[name]
            if spec.is_activated and spec.is_activated(self):
                return name
        return "unknown"

    def prompt(self, *args, **kwargs):
        text = super().prompt(*args, **kwargs)
        current_mode_spec = self.current_mode_spec
        if current_mode_spec.callback:
            text = current_mode_spec.callback(self)

        return text


def apply_settings(session, settings):
    setoption("prompt", settings.prompt)

    if settings.auto_width:
        output_width = session.app.output.get_size().columns
        if output_width:
            setoption("width", output_width)

    # necessary on windows
    setoption("menu.graphics", False)

    def askpass(message):
        app = session.app
        if app.is_running:
            from getpass import getpass
            return getpass(message)
        else:
            from prompt_toolkit import prompt
            return prompt(message, is_password=True)

    if not roption("askpass"):
        setoption("askpass", robject(askpass, convert=True))

    # enables completion of installed package names
    if rcopy(rcall(("utils", "rc.settings"), "ipck")) is None:
        rcall(("utils", "rc.settings"), ipck=True)


def create_radian_prompt_session(options, settings):

    local_history_file = settings.local_history_file
    global_history_file = settings.global_history_file

    if options.no_history:
        history = ModalInMemoryHistory()
    elif not options.global_history and os.path.exists(local_history_file):
        history = ModalFileHistory(os.path.abspath(local_history_file), settings.history_size)
    else:
        history_file = os.path.join(os.path.expanduser(global_history_file))
        history_file = os.path.expandvars(history_file)
        history_file_dir = os.path.dirname(history_file)
        if not os.path.exists(history_file_dir):
            os.makedirs(history_file_dir, 0o700)
        history = ModalFileHistory(history_file, settings.history_size)

    if is_windows():
        output = None
    else:
        output = CustomOutput.from_pty(sys.stdout, term=get_term_environment_variable())

    def vi_mode_prompt():
        if session.editing_mode == EditingMode.VI and settings.show_vi_mode_prompt:
            im = session.app.vi_state.input_mode.value
            vi_mode_prompt = settings.vi_mode_prompt
            if isinstance(vi_mode_prompt, str):
                return vi_mode_prompt.format(str(im)[3:6])
            else:
                return vi_mode_prompt[str(im)[3:6]]
        return ""

    def message():
        if session.current_mode_spec.prompt_message:
            return ANSI(
                vi_mode_prompt() + session.current_mode_spec.prompt_message(session._prompt_message)
                )
        else:
            return session._prompt_message

    if settings.editing_mode in ["vim", "vi"]:
        editing_mode = EditingMode.VI
    else:
        editing_mode = EditingMode.EMACS

    session = RadianPromptSession(
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
        auto_suggest=AutoSuggestFromHistory() if settings.auto_suggest else None
    )

    input_processors = []
    if settings.highlight_matching_bracket:
        input_processors.append(HighlightMatchingBracketProcessor())

    r_key_bindings = create_r_key_bindings(prase_text_complete)

    session.register_mode(
        name="r",
        prompt_message=lambda x: x,
        is_activated=lambda session: session._prompt_message == settings.prompt,
        history_book="r",
        insert_new_line=True,
        multiline=settings.indent_lines,
        completer=RCompleter(timeout=settings.completion_timeout),
        complete_while_typing=settings.complete_while_typing,
        lexer=PygmentsLexer(SLexer),
        tempfile_suffix=".R",
        input_processors=input_processors,
        key_bindings=create_key_bindings(),
        prompt_key_bindings=r_key_bindings
    )

    browse_level = [""]

    def browse_activator(session):
        message = session._prompt_message
        if BROWSE_PATTERN.match(message):
            browse_level[0] = BROWSE_PATTERN.match(message).group(1)
            return True
        else:
            return False

    class BrowseValidator(Validator):
        """
        As a pre-accept processor.
        """
        def validate(self, document):
            text = document.text
            if settings.history_ignore_browser_commands:
                if text.strip() in ["n", "s", "f", "c", "cont", "Q", "where", "help"]:
                    session.add_history = False

    session.register_mode(
        name="browse",
        is_activated=browse_activator,
        prompt_message=lambda _: settings.browse_prompt.format(browse_level[0]),
        history_book="r",
        insert_new_line=True,
        multiline=settings.indent_lines,
        completer=RCompleter(timeout=settings.completion_timeout),
        complete_while_typing=settings.complete_while_typing,
        validator=BrowseValidator(),
        lexer=PygmentsLexer(SLexer),
        tempfile_suffix=".R",
        input_processors=input_processors,
        prompt_key_bindings=r_key_bindings
    )

    def shell_process_text(session):
        text = session.default_buffer.text
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
        prompt_key_bindings=create_shell_key_bindings()
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
        input_processors=[]
    )

    def get_inputhook():
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

    # make testing more robust
    if "RADIAN_NO_INPUTHOOK" not in os.environ:
        set_eventloop_with_inputhook(get_inputhook())

    apply_settings(session, settings)

    return session
