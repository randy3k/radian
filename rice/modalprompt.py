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
    KeyBindings, DynamicKeyBindings, merge_key_bindings, ConditionalKeyBindings
from prompt_toolkit.keys import Keys
from prompt_toolkit.layout import Window, HSplit, FloatContainer, Float
from prompt_toolkit.layout.containers import ConditionalContainer
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
from prompt_toolkit.layout.dimension import Dimension
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.layout.lexers import DynamicLexer
from prompt_toolkit.layout.margins import PromptMargin
from prompt_toolkit.layout.menus import MultiColumnCompletionsMenu
from prompt_toolkit.layout.processors import \
    DynamicProcessor, PasswordProcessor, ConditionalProcessor, AppendAutoSuggestion, \
    HighlightSearchProcessor, HighlightSelectionProcessor, HighlightMatchingBracketProcessor, \
    DisplayMultipleCursors, BeforeInput, ReverseSearchProcessor, ShowArg, merge_processors
from prompt_toolkit.layout.utils import explode_text_fragments
from prompt_toolkit.layout.widgets.toolbars import SearchToolbar
from prompt_toolkit.output.defaults import get_default_output
from prompt_toolkit.shortcuts.prompt import _split_multiline_prompt
from prompt_toolkit.styles import default_style, DynamicStyle, merge_styles
from prompt_toolkit.utils import suspend_to_background_supported
from prompt_toolkit.utils import is_windows

from .modalbuffer import ModalBuffer

import contextlib
import threading
import time
import sys


def create_prompt_bindings():
    """
    Create the KeyBindings for a prompt application.
    """
    kb = KeyBindings()
    handle = kb.add
    default_focussed = has_focus(DEFAULT_BUFFER)

    @handle('enter', filter=default_focussed)
    def _(event):
        " Accept input when enter has been pressed. "
        event.current_buffer.validate_and_handle()

    @handle('c-c', filter=default_focussed)
    def _(event):
        " Abort when Control-C has been pressed. "
        event.app.abort()

    @Condition
    def ctrl_d_condition():
        """ Ctrl-D binding is only active when the default buffer is selected
        and empty. """
        app = get_app()
        return (app.current_buffer.name == DEFAULT_BUFFER and
                not app.current_buffer.text)

    @handle('c-d', filter=ctrl_d_condition & default_focussed)
    def _(event):
        " Exit when Control-D has been pressed. "
        event.app.exit()

    suspend_supported = Condition(suspend_to_background_supported)


    @handle('c-z', filter=suspend_supported)
    def _(event):
        """
        Suspend process to background.
        """
        event.app.suspend_to_background()

    return kb


class ModalPromptBase(object):
    _message = {}
    _prompt_mode = None

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


if not is_windows():
    from prompt_toolkit.input.vt100 import Vt100Input

    class CustomVt100Input(Vt100Input):
        @property
        def responds_to_cpr(self):
            return False


class ModalPrompt(ModalPromptBase):
    multiline = True
    lexer = None
    enable_open_in_editor = False
    reserve_space_for_menu = 4
    completer = None
    complete_while_typing = True
    style = None
    history = None
    prompt_continuation = None
    tempfile_suffix = '.R'

    def __init__(
            self,
            editing_mode=EditingMode.EMACS,
            history=None,
            lexer=None,
            style=None,
            completer=None,
            extra_key_bindings=None,
            input=None,
            output=None,
            on_render=None,
            on_resize=None):

        self.history = history
        self.lexer = lexer
        self.style = None
        self.completer = completer
        self.extra_key_bindings = extra_key_bindings
        if not is_windows():
            self.input = input or CustomVt100Input(sys.stdin)
        else:
            self.input = input or get_default_input()
        self.output = output or get_default_output()

        self.on_render = on_render
        self.on_resize = on_resize

        self.app, self._default_buffer, self._default_buffer_control = \
            self._create_application(editing_mode)

        self.app.mp = self

    def _create_application(self, editing_mode):

        # Create functions that will dynamically split the prompt. (If we have
        # a multiline prompt.)
        has_before_fragments, get_prompt_text_1, get_prompt_text_2 = \
            _split_multiline_prompt(self._get_prompt)

        default_buffer = ModalBuffer(
            name=DEFAULT_BUFFER,
            complete_while_typing=Condition(lambda: self.complete_while_typing),
            completer=DynamicCompleter(lambda: self.completer),
            history=self.history,
            get_tempfile_suffix=lambda: self.tempfile_suffix)

        search_buffer = Buffer(name=SEARCH_BUFFER)

        search_toolbar = SearchToolbar(search_buffer)

        input_processor = merge_processors([
            ConditionalProcessor(
                HighlightSearchProcessor(preview_search=True),
                has_focus(search_buffer)),
            HighlightSelectionProcessor(),
            HighlightMatchingBracketProcessor(),
            DisplayMultipleCursors()
        ])

        default_buffer_control = BufferControl(
            buffer=default_buffer,
            search_buffer_control=search_toolbar.control,
            input_processor=input_processor,
            lexer=DynamicLexer(lambda: self.lexer),
            preview_search=True)

        default_buffer_window = Window(
            default_buffer_control,
            height=self._get_default_buffer_control_height,
            left_margins=[
                PromptMargin(get_prompt_text_2, self._get_continuation)
            ],
            wrap_lines=True)

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
                Window(FormattedTextControl(self._get_arg_text), height=1), has_arg),
            search_toolbar
        ])

        # Default key bindings.
        open_in_editor_bindings = load_open_in_editor_bindings()
        prompt_bindings = create_prompt_bindings()

        # Create application
        application = Application(
            layout=Layout(layout, default_buffer_window),
            style=merge_styles([
                default_style(),
                DynamicStyle(lambda: self.style),
            ]),
            key_bindings=merge_key_bindings([
                merge_key_bindings([
                    ConditionalKeyBindings(
                        open_in_editor_bindings,
                        to_filter(self.enable_open_in_editor) & has_focus(DEFAULT_BUFFER)),
                    prompt_bindings
                ]),
                DynamicKeyBindings(lambda: self.extra_key_bindings),
            ]),
            editing_mode=editing_mode,
            reverse_vi_search_direction=True,
            on_render=self.on_render,
            on_resize=self.on_resize,
            input=self.input,
            output=self.output)

        return application, default_buffer, default_buffer_control

    def prompt(self, **kwargs):

        _fields = set(kwargs.keys()).intersection(set(self.__dict__.keys()))
        backup = dict((name, getattr(self, name)) for name in _fields)

        # Take settings from 'prompt'-arguments.
        for name in _fields:
            value = kwargs[name]
            if value is not None:
                setattr(self, name, value)

        try:
            self._default_buffer.reset(Document(""))
            return self.app.run()
        finally:
            for name in _fields:
                setattr(self, name, backup[name])

    @property
    def editing_mode(self):
        return self.app.editing_mode

    @editing_mode.setter
    def editing_mode(self, value):
        self.app.editing_mode = value

    def _get_default_buffer_control_height(self):
        # If there is an autocompletion menu to be shown, make sure that our
        # layout has at least a minimal height in order to display it.
        space = self.reserve_space_for_menu

        if space and not get_app().is_done:
            buff = self._default_buffer
            if buff.complete_while_typing() or buff.complete_state is not None:
                return Dimension(min=space)

        return Dimension()

    def _get_prompt(self):
        return to_formatted_text(self.message, style='class:prompt')

    def _get_continuation(self, width):
        prompt_continuation = self.prompt_continuation

        if callable(prompt_continuation):
            prompt_continuation = prompt_continuation(width)

        return to_formatted_text(
            prompt_continuation, style='class:prompt-continuation')

    def _get_arg_text(self):
        arg = self.app.key_processor.arg
        if arg == '-':
            arg = '-1'

        return [
            ('class:arg-toolbar', 'Repeat: '),
            ('class:arg-toolbar.text', arg)
        ]
