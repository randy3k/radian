from __future__ import unicode_literals

from prompt_toolkit.application import Application
from prompt_toolkit.application.current import get_app
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.completion import DynamicCompleter
from prompt_toolkit.document import Document
from prompt_toolkit.enums import DEFAULT_BUFFER, SEARCH_BUFFER, EditingMode
from prompt_toolkit.filters import has_focus, to_filter, Condition, has_arg
from prompt_toolkit.formatted_text import to_formatted_text
from prompt_toolkit.input.defaults import get_default_input
from prompt_toolkit.key_binding.bindings.open_in_editor import load_open_in_editor_bindings
from prompt_toolkit.key_binding.key_bindings import \
    DynamicKeyBindings, merge_key_bindings, ConditionalKeyBindings
from prompt_toolkit.layout import Window, HSplit, FloatContainer, Float
from prompt_toolkit.layout.containers import ConditionalContainer
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
from prompt_toolkit.layout.dimension import Dimension
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.layout.margins import PromptMargin
from prompt_toolkit.layout.menus import MultiColumnCompletionsMenu
from prompt_toolkit.layout.processors import \
    HighlightIncrementalSearchProcessor, HighlightSelectionProcessor, \
    HighlightMatchingBracketProcessor, DisplayMultipleCursors
from prompt_toolkit.lexers import DynamicLexer
from prompt_toolkit.widgets.toolbars import SearchToolbar
from prompt_toolkit.output import get_default_output, ColorDepth
from prompt_toolkit.shortcuts.prompt import _split_multiline_prompt
from prompt_toolkit.styles import DynamicStyle
import os

from .modalbuffer import ModalBuffer
from .keybinding import create_prompt_bindings


class ModalPrompt(object):
    multiline = True
    lexer = None
    enable_open_in_editor = False
    reserve_space_for_menu = 6
    completer = None
    complete_while_typing = True
    style = None
    history = None
    prompt_continuation = None
    inputhook = None

    _message = {}
    _prompt_mode = None

    def __init__(
            self,
            editing_mode=EditingMode.EMACS,
            history=None,
            lexer=None,
            style=None,
            completer=None,
            extra_key_bindings=None,
            tempfile_suffix=None,
            input=None,
            output=None,
            after_render=None,
            accept=None,
            inputhook=None):

        self.editing_mode = editing_mode
        self.history = history
        self.lexer = lexer
        self.style = style
        self.completer = completer
        self.extra_key_bindings = extra_key_bindings
        self.tempfile_suffix = tempfile_suffix
        self.input = input or get_default_input()
        self.output = output or get_default_output()
        self.after_render = after_render
        self.accept = accept
        self.inputhook = inputhook
        self.create_application()

    def set_prompt_mode_message(self, mode, message):
        self._message[mode] = message

    def prompt_mode_message(self, mode):
        message = self._message[mode]
        return message

    @property
    def prompt_mode(self):
        return self._prompt_mode

    @prompt_mode.setter
    def prompt_mode(self, mode):
        self._prompt_mode = mode

    @property
    def message(self):
        message = self._message[self.prompt_mode]
        return message

    def formatted_message(self):
        return to_formatted_text(self.message, style='class:prompt')

    def create_layout(self):
        # Create functions that will dynamically split the prompt. (If we have
        # a multiline prompt.)
        has_before_fragments, get_prompt_text_1, get_prompt_text_2 = \
            _split_multiline_prompt(self.formatted_message)

        default_buffer = ModalBuffer(
            name=DEFAULT_BUFFER,
            complete_while_typing=Condition(lambda: self.complete_while_typing),
            completer=DynamicCompleter(lambda: self.completer),
            history=self.history,
            enable_history_search=True,
            accept_handler=self.accept,
            get_tempfile_suffix=lambda: self.tempfile_suffix)

        search_buffer = Buffer(name=SEARCH_BUFFER)
        search_toolbar = SearchToolbar(search_buffer)

        # Create processors list.
        all_input_processors = [
            HighlightIncrementalSearchProcessor(),
            HighlightSelectionProcessor(),
            DisplayMultipleCursors(),
            HighlightMatchingBracketProcessor()
        ]

        default_buffer_control = BufferControl(
            buffer=default_buffer,
            search_buffer_control=search_toolbar.control,
            input_processors=all_input_processors,
            include_default_input_processors=False,
            lexer=DynamicLexer(lambda: self.lexer),
            preview_search=True)

        def get_default_buffer_control_height():
            # If there is an autocompletion menu to be shown, make sure that our
            # layout has at least a minimal height in order to display it.
            space = self.reserve_space_for_menu

            if space and not get_app().is_done:
                buff = default_buffer
                if buff.complete_while_typing() or buff.complete_state is not None:
                    return Dimension(min=space)
            return Dimension()

        def get_continuation(width):
            prompt_continuation = self.prompt_continuation

            if callable(prompt_continuation):
                prompt_continuation = prompt_continuation(width)

            return to_formatted_text(
                prompt_continuation, style='class:prompt-continuation')

        default_buffer_window = Window(
            default_buffer_control,
            height=get_default_buffer_control_height,
            left_margins=[
                PromptMargin(get_prompt_text_2, get_continuation)
            ],
            wrap_lines=True)

        def get_arg_text():
            arg = self.app.key_processor.arg
            if arg == '-':
                arg = '-1'

            return [
                ('class:arg-toolbar', 'Repeat: '),
                ('class:arg-toolbar.text', arg)
            ]

        # Build the layout.
        layout = HSplit([
            # The main input, with completion menus floating on top of it.
            FloatContainer(
                HSplit([
                    ConditionalContainer(
                        Window(
                            FormattedTextControl(get_prompt_text_1),
                            dont_extend_height=True),
                        Condition(has_before_fragments)
                    ),
                    default_buffer_window,
                ]),
                [
                    # Completion menus.
                    Float(xcursor=True,
                          ycursor=True,
                          content=MultiColumnCompletionsMenu(
                              show_meta=True,
                              extra_filter=has_focus(default_buffer)))
                ]
            ),

            ConditionalContainer(
                Window(FormattedTextControl(get_arg_text), height=1), has_arg),
            search_toolbar
        ])

        return Layout(layout, default_buffer_window)

    def create_application(self):

        # Default key bindings.
        open_in_editor_bindings = load_open_in_editor_bindings()
        prompt_bindings = create_prompt_bindings()

        self.app = Application(
            layout=self.create_layout(),
            style=DynamicStyle(lambda: self.style),
            include_default_pygments_style=True,
            color_depth=ColorDepth.default(term=os.environ.get("TERM")),
            key_bindings=merge_key_bindings([
                merge_key_bindings([
                    ConditionalKeyBindings(
                        open_in_editor_bindings,
                        to_filter(self.enable_open_in_editor) & has_focus(DEFAULT_BUFFER)),
                    prompt_bindings
                ]),
                DynamicKeyBindings(lambda: self.extra_key_bindings),
            ]),
            editing_mode=self.editing_mode,
            reverse_vi_search_direction=True,
            after_render=self.after_render,
            input=self.input,
            output=self.output)

        self.app.mp = self

    def run(self, **kwargs):
        _fields = set(kwargs.keys()).intersection(set(self.__dict__.keys()))
        backup = dict((name, getattr(self, name)) for name in _fields)

        for name in _fields:
            value = kwargs[name]
            if value is not None:
                setattr(self, name, value)

        try:
            self.app.current_buffer.reset(Document(""))
            return self.app.run(inputhook=self.inputhook)
        finally:
            for name in _fields:
                setattr(self, name, backup[name])
