from __future__ import unicode_literals

from prompt_toolkit.application import Application
from prompt_toolkit.application.current import get_app
from prompt_toolkit.auto_suggest import DynamicAutoSuggest
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.clipboard import DynamicClipboard, InMemoryClipboard
from prompt_toolkit.completion import DynamicCompleter
from prompt_toolkit.document import Document
from prompt_toolkit.enums import DEFAULT_BUFFER, SEARCH_BUFFER, EditingMode
from prompt_toolkit.filters import is_done, has_focus, renderer_height_is_known, to_filter, Condition, has_arg
from prompt_toolkit.formatted_text import to_formatted_text
from prompt_toolkit.history import InMemoryHistory, DynamicHistory
from prompt_toolkit.input.defaults import get_default_input
from prompt_toolkit.key_binding.bindings.auto_suggest import load_auto_suggest_bindings
from prompt_toolkit.key_binding.bindings.completion import display_completions_like_readline
from prompt_toolkit.key_binding.bindings.open_in_editor import load_open_in_editor_bindings
from prompt_toolkit.key_binding.key_bindings import KeyBindings, DynamicKeyBindings, merge_key_bindings, ConditionalKeyBindings, KeyBindingsBase
from prompt_toolkit.layout import Window, HSplit, FloatContainer, Float
from prompt_toolkit.layout.containers import ConditionalContainer, Align
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
from prompt_toolkit.layout.dimension import Dimension
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.layout.lexers import DynamicLexer
from prompt_toolkit.layout.margins import PromptMargin, ConditionalMargin
from prompt_toolkit.layout.menus import CompletionsMenu, MultiColumnCompletionsMenu
from prompt_toolkit.layout.processors import Processor, DynamicProcessor, PasswordProcessor, ConditionalProcessor, AppendAutoSuggestion, HighlightSearchProcessor, HighlightSelectionProcessor, HighlightMatchingBracketProcessor, DisplayMultipleCursors, BeforeInput, ReverseSearchProcessor, ShowArg, merge_processors
from prompt_toolkit.layout.utils import explode_text_fragments
from prompt_toolkit.layout.widgets.toolbars import ValidationToolbar, SystemToolbar, SearchToolbar
from prompt_toolkit.output.defaults import get_default_output
from prompt_toolkit.styles import default_style, DynamicStyle, merge_styles
from prompt_toolkit.utils import suspend_to_background_supported
from prompt_toolkit.validation import DynamicValidator
from prompt_toolkit.utils import is_windows


import contextlib
import threading
import time
import sys


def _split_multiline_prompt(get_prompt_text):
    """
    Take a `get_prompt_text` function and return three new functions instead.
    One that tells whether this prompt consists of multiple lines; one that
    returns the fragments to be shown on the lines above the input; and another
    one with the fragments to be shown at the first line of the input.
    """
    def has_before_fragments():
        for fragment, char in get_prompt_text():
            if '\n' in char:
                return True
        return False

    def before():
        result = []
        found_nl = False
        for fragment, char in reversed(explode_text_fragments(get_prompt_text())):
            if found_nl:
                result.insert(0, (fragment, char))
            elif char == '\n':
                found_nl = True
        return result

    def first_input_line():
        result = []
        for fragment, char in reversed(explode_text_fragments(get_prompt_text())):
            if char == '\n':
                break
            else:
                result.insert(0, (fragment, char))
        return result

    return has_before_fragments, before, first_input_line


def _true(value):
    " Test whether `value` is True. In case of a Filter, call it. "
    return to_filter(value)()


class CompleteStyle:
    " How to display autocompletions for the prompt. "
    COLUMN = 'COLUMN'
    MULTI_COLUMN = 'MULTI_COLUMN'
    READLINE_LIKE = 'READLINE_LIKE'


class MultiPromptBase(object):
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


class MultiPrompt(MultiPromptBase):
    default = ""
    multiline = True
    complete_while_typing = True
    enable_suspend = True
    wrap_lines = True
    is_password = False
    validate_while_typing = False
    enable_history_search = False
    lexer = None
    enable_system_prompt = False
    enable_suspend = True
    enable_open_in_editor = False
    validator = None
    reserve_space_for_menu = 8
    completer = None
    complete_style = None
    auto_suggest = None
    style = None
    history = None
    clipboard = InMemoryClipboard()
    prompt_continuation = None
    rprompt = None
    bottom_toolbar = None
    mouse_support = False
    tempfile_suffix = '.R'
    refresh_interval = 0

    def __init__(
            self,
            editing_mode=EditingMode.EMACS,
            history=None,
            lexer=None,
            completer=None,
            extra_key_bindings=None,
            input=None,
            output=None):

        self.history = history or InMemoryHistory()
        self.lexer = lexer
        self.completer = completer
        self.extra_key_bindings = extra_key_bindings
        if not is_windows():
            self.input = input or CustomVt100Input(sys.stdin)
        else:
            self.input = input or get_default_input()
        self.output = output or get_default_output()

        self.app, self._default_buffer, self._default_buffer_control = \
            self._create_application(editing_mode)

        self.app.mp = self

    def _create_application(self, editing_mode):
        def dyncond(attr_name):
            """
            Dynamically take this setting from this 'Prompt' class.
            `attr_name` represents an attribute name of this class. Its value
            can either be a boolean or a `Filter`.

            This returns something that can be used as either a `Filter`
            or `Filter`.
            """
            @Condition
            def dynamic():
                value = getattr(self, attr_name)
                return to_filter(value)()
            return dynamic

        # Create functions that will dynamically split the prompt. (If we have
        # a multiline prompt.)
        has_before_fragments, get_prompt_text_1, get_prompt_text_2 = \
            _split_multiline_prompt(self._get_prompt)

        # Create buffers list.
        def accept(buff):
            """ Accept the content of the default buffer. This is called when
            the validation succeeds. """
            self.app.set_return_value(buff.document.text)

            # Reset content before running again.
            self.app.pre_run_callables.append(buff.reset)

        default_buffer = Buffer(
            name=DEFAULT_BUFFER,
                # Make sure that complete_while_typing is disabled when
                # enable_history_search is enabled. (First convert to Filter,
                # to avoid doing bitwise operations on bool objects.)
            complete_while_typing=Condition(lambda:
                _true(self.complete_while_typing) and not
                _true(self.enable_history_search) and not
                self.complete_style == CompleteStyle.READLINE_LIKE),
            validate_while_typing=dyncond('validate_while_typing'),
            enable_history_search=dyncond('enable_history_search'),
            validator=DynamicValidator(lambda: self.validator),
            completer=DynamicCompleter(lambda: self.completer),
            history=DynamicHistory(lambda: self.history),
            auto_suggest=DynamicAutoSuggest(lambda: self.auto_suggest),
            accept_handler=accept,
            get_tempfile_suffix=lambda: self.tempfile_suffix)

        search_buffer = Buffer(name=SEARCH_BUFFER)

        # Create processors list.
        input_processor = merge_processors([
            ConditionalProcessor(
                # By default, only highlight search when the search
                # input has the focus. (Note that this doesn't mean
                # there is no search: the Vi 'n' binding for instance
                # still allows to jump to the next match in
                # navigation mode.)
                HighlightSearchProcessor(preview_search=True),
                has_focus(search_buffer)),
            HighlightSelectionProcessor(),
            HighlightMatchingBracketProcessor(),
            ConditionalProcessor(AppendAutoSuggestion(), has_focus(default_buffer) & ~is_done),
            ConditionalProcessor(PasswordProcessor(), dyncond('is_password')),
            DisplayMultipleCursors(),

            # For single line mode, show the prompt before the input.
            ConditionalProcessor(
                merge_processors([
                    BeforeInput(get_prompt_text_2),
                    ShowArg(),
                ]),
                ~dyncond('multiline'))
        ])

        # Create bottom toolbars.
        bottom_toolbar = ConditionalContainer(
            Window(FormattedTextControl(
                        lambda: self.bottom_toolbar,
                        style='class:bottom-toolbar.text'),
                   style='class:bottom-toolbar',
                   height=Dimension.exact(1)),
            filter=~is_done & renderer_height_is_known &
                    Condition(lambda: self.bottom_toolbar is not None))

        search_toolbar = SearchToolbar(search_buffer)
        search_buffer_control = BufferControl(
            buffer=search_buffer,
            input_processor=merge_processors([
                ReverseSearchProcessor(),
                ShowArg(),
            ]))

        system_toolbar = SystemToolbar()

        def get_search_buffer_control():
            " Return the UIControl to be focussed when searching start. "
            if _true(self.multiline):
                return search_toolbar.control
            else:
                return search_buffer_control

        default_buffer_control = BufferControl(
            buffer=default_buffer,
            get_search_buffer_control=get_search_buffer_control,
            input_processor=input_processor,
            lexer=DynamicLexer(lambda: self.lexer),
            preview_search=True)

        default_buffer_window = Window(
            default_buffer_control,
            height=self._get_default_buffer_control_height,
            left_margins=[
                # In multiline mode, use the window margin to display
                # the prompt and continuation fragments.
                ConditionalMargin(
                    PromptMargin(get_prompt_text_2, self._get_continuation),
                    filter=dyncond('multiline'),
                )
            ],
            wrap_lines=dyncond('wrap_lines'))

        @Condition
        def multi_column_complete_style():
            return self.complete_style == CompleteStyle.MULTI_COLUMN

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
                    ConditionalContainer(
                        default_buffer_window,
                        Condition(lambda:
                            get_app().layout.current_control != search_buffer_control),
                    ),
                    ConditionalContainer(
                        Window(search_buffer_control),
                        Condition(lambda:
                            get_app().layout.current_control == search_buffer_control),
                    ),
                ]),
                [
                    # Completion menus.
                    Float(xcursor=True,
                          ycursor=True,
                          content=CompletionsMenu(
                              max_height=16,
                              scroll_offset=1,
                              extra_filter=has_focus(default_buffer) &
                                  ~multi_column_complete_style)),
                    Float(xcursor=True,
                          ycursor=True,
                          content=MultiColumnCompletionsMenu(
                              show_meta=True,
                              extra_filter=has_focus(default_buffer) &
                                  multi_column_complete_style))
                ]
            ),
            ValidationToolbar(),
            ConditionalContainer(
                system_toolbar,
                dyncond('enable_system_prompt') & ~is_done),

            # In multiline mode, we use two toolbars for 'arg' and 'search'.
            ConditionalContainer(
                Window(FormattedTextControl(self._get_arg_text), height=1),
                dyncond('multiline') & has_arg),
            ConditionalContainer(search_toolbar, dyncond('multiline')),
            bottom_toolbar,
        ])

        # Default key bindings.
        auto_suggest_bindings = load_auto_suggest_bindings()
        open_in_editor_bindings = load_open_in_editor_bindings()
        prompt_bindings = self._create_prompt_bindings()

        def on_render(app):
            if app.is_aborting:
                self.output.write("\n")

        # Create application
        application = Application(
            layout=Layout(layout, default_buffer_window),
            style=merge_styles([
                default_style(),
                DynamicStyle(lambda: self.style),
            ]),
            clipboard=DynamicClipboard(lambda: self.clipboard),
            key_bindings=merge_key_bindings([
                merge_key_bindings([
                    auto_suggest_bindings,
                    ConditionalKeyBindings(open_in_editor_bindings,
                        dyncond('enable_open_in_editor') &
                        has_focus(DEFAULT_BUFFER)),
                    prompt_bindings
                ]),
                ConditionalKeyBindings(
                    system_toolbar.get_global_key_bindings(),
                    dyncond('enable_system_prompt')),
                DynamicKeyBindings(lambda: self.extra_key_bindings),
            ]),
            mouse_support=dyncond('mouse_support'),
            editing_mode=editing_mode,
            reverse_vi_search_direction=True,
            on_render=on_render,

            # I/O.
            input=self.input,
            output=self.output)

        return application, default_buffer, default_buffer_control

    def _create_prompt_bindings(self):
        """
        Create the KeyBindings for a prompt application.
        """
        kb = KeyBindings()
        handle = kb.add
        default_focussed = has_focus(DEFAULT_BUFFER)

        @Condition
        def do_accept():
            return (not _true(self.multiline) and
                    self.app.layout.current_control == self._default_buffer_control)

        @handle('enter', filter=do_accept & default_focussed)
        def _(event):
            " Accept input when enter has been pressed. "
            self._default_buffer.validate_and_handle()

        @Condition
        def readline_complete_style():
            return self.complete_style == CompleteStyle.READLINE_LIKE

        @handle('tab', filter=readline_complete_style & default_focussed)
        def _(event):
            " Display completions (like readline). "
            display_completions_like_readline(event)

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

        @Condition
        def enable_suspend():
            return to_filter(self.enable_suspend)()

        @handle('c-z', filter=suspend_supported & enable_suspend)
        def _(event):
            """
            Suspend process to background.
            """
            event.app.suspend_to_background()

        return kb

    @contextlib.contextmanager
    def _auto_refresh_context(self):
        " Return a context manager for the auto-refresh loop. "
        done = [False]  # nonlocal

        # Enter.

        def run():
            while not done[0]:
                time.sleep(self.refresh_interval)
                self.app.invalidate()

        if self.refresh_interval:
            t = threading.Thread(target=run)
            t.daemon = True
            t.start()

        try:
            yield
        finally:
            # Exit.
            done[0] = True

    def prompt(self, **kwargs):

        _fields = set(kwargs.keys()).intersection(set(self.__dict__.keys()))
        backup = dict((name, getattr(self, name)) for name in _fields)

        # Take settings from 'prompt'-arguments.
        for name in _fields:
            value = kwargs[name]
            if value is not None:
                setattr(self, name, value)

        with self._auto_refresh_context():
            try:
                self._default_buffer.reset(Document(self.default))
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
        if (self.completer is not None and
                self.complete_style != CompleteStyle.READLINE_LIKE):
            space = self.reserve_space_for_menu
        else:
            space = 0

        if space and not get_app().is_done:
            buff = self._default_buffer

            # Reserve the space, either when there are completions, or when
            # `complete_while_typing` is true and we expect completions very
            # soon.
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
