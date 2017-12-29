from __future__ import unicode_literals
import re

from prompt_toolkit.application.current import get_app

from prompt_toolkit.keys import Keys
from prompt_toolkit.key_binding.key_bindings import KeyBindings
from prompt_toolkit.key_binding.bindings.named_commands import backward_delete_char
from prompt_toolkit.filters import Condition, has_focus, \
    emacs_insert_mode, vi_insert_mode, in_paste_mode, app
from prompt_toolkit.enums import DEFAULT_BUFFER
from prompt_toolkit.utils import suspend_to_background_supported

from . import interface


default_focussed = has_focus(DEFAULT_BUFFER)
insert_mode = vi_insert_mode | emacs_insert_mode


def prompt_mode(*modes):
    return Condition(lambda: get_app().mp.prompt_mode in modes)


@Condition
def prase_complete():
    app = get_app()
    return interface.prase_input_complete(app.current_buffer.text)


def preceding_text(pattern):
    m = re.compile(pattern)

    def _preceding_text():
        app = get_app()
        return bool(m.match(app.current_buffer.document.current_line_before_cursor))

    return Condition(_preceding_text)


def following_text(pattern):
    m = re.compile(pattern)

    def _following_text():
        app = get_app()
        return bool(m.match(app.current_buffer.document.current_line_after_cursor))

    return Condition(_following_text)


@Condition
def is_begin_of_buffer():
    return get_app().current_buffer.cursor_position == 0


@Condition
def is_end_of_buffer():
    app = get_app()
    return app.current_buffer.cursor_position == len(app.current_buffer.text)


@Condition
def auto_indentation():
    return get_app().auto_indentation


@Condition
def auto_match():
    return get_app().auto_match

@Condition
def has_complete_index():
    app = get_app()
    cs = app.current_buffer.complete_state
    return cs and cs.complete_index is not None


def if_no_repeat(event):
    return not event.is_repeat


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


def create_keybindings():
    kb = KeyBindings()
    handle = kb.add

    # r mode
    @handle(';', filter=insert_mode & default_focussed & prompt_mode("r") & is_begin_of_buffer)
    def _(event):
        event.app.mp.prompt_mode = "shell"
        event.app._redraw()

    @handle('c-j', filter=insert_mode & default_focussed & prompt_mode("r", "browse"))
    @handle('enter', filter=insert_mode & default_focussed & prompt_mode("r", "browse"))
    def _(event):
        should_indent = event.current_buffer.document.char_before_cursor in ["{", "[", "("]
        copy_margin = not in_paste_mode() and event.app.auto_indentation
        event.current_buffer.newline(copy_margin=copy_margin)
        if should_indent and event.app.auto_indentation:
            tab_size = event.app.tab_size
            event.current_buffer.insert_text(" " * tab_size)

    @handle('c-j', filter=insert_mode & default_focussed & prompt_mode("r") & prase_complete)
    @handle('enter', filter=insert_mode & default_focussed & prompt_mode("r") & prase_complete)
    def _(event):
        event.current_buffer.validate_and_handle()

    # auto match
    @handle('(', filter=insert_mode & default_focussed & prompt_mode("r", "browse") & auto_match & following_text(r"[)}\]]|$"))
    def _(event):
        event.current_buffer.insert_text("()")
        event.current_buffer.cursor_left()

    @handle('[', filter=insert_mode & default_focussed & prompt_mode("r", "browse") & auto_match & following_text(r"[)}\]]|$"))
    def _(event):
        event.current_buffer.insert_text("[]")
        event.current_buffer.cursor_left()

    @handle('{', filter=insert_mode & default_focussed & prompt_mode("r", "browse") & auto_match & following_text(r"[)}\]]|$"))
    def _(event):
        event.current_buffer.insert_text("{}")
        event.current_buffer.cursor_left()

    @handle('"', filter=insert_mode & default_focussed & prompt_mode("r", "browse") & auto_match & following_text(r"[)}\]]|$"))
    def _(event):
        event.current_buffer.insert_text('""')
        event.current_buffer.cursor_left()

    @handle("'", filter=insert_mode & default_focussed & prompt_mode("r", "browse") & auto_match & following_text(r"[)}\]]|$"))
    def _(event):
        event.current_buffer.insert_text("''")
        event.current_buffer.cursor_left()

    @handle(')', filter=insert_mode & default_focussed & prompt_mode("r", "browse") & auto_match & following_text(r"^\)"))
    @handle(']', filter=insert_mode & default_focussed & prompt_mode("r", "browse") & auto_match & following_text(r"^\]"))
    @handle('}', filter=insert_mode & default_focussed & prompt_mode("r", "browse") & auto_match & following_text(r"^\}"))
    @handle('"', filter=insert_mode & default_focussed & prompt_mode("r", "browse") & auto_match & following_text("^\""))
    @handle("'", filter=insert_mode & default_focussed & prompt_mode("r", "browse") & auto_match & following_text("^'"))
    def _(event):
        event.current_buffer.cursor_right()

    @handle('backspace', filter=insert_mode & default_focussed & prompt_mode("r", "browse") & preceding_text(r".*\($") & following_text(r"^\)"))
    @handle('backspace', filter=insert_mode & default_focussed & prompt_mode("r", "browse") & preceding_text(r".*\[$") & following_text(r"^\]"))
    @handle('backspace', filter=insert_mode & default_focussed & prompt_mode("r", "browse") & preceding_text(r".*\{$") & following_text(r"^\}"))
    @handle('backspace', filter=insert_mode & default_focussed & prompt_mode("r", "browse") & preceding_text('.*"$') & following_text('^"'))
    @handle('backspace', filter=insert_mode & default_focussed & prompt_mode("r", "browse") & preceding_text(r".*'$") & following_text(r"^'"))
    def _(event):
        event.current_buffer.delete()
        event.current_buffer.delete_before_cursor()

    # indentation
    @handle('}', filter=insert_mode & default_focussed & prompt_mode("r", "browse") & auto_indentation & preceding_text(r"^\s*$"))
    @handle(']', filter=insert_mode & default_focussed & prompt_mode("r", "browse") & auto_indentation & preceding_text(r"^\s*$"))
    @handle(')', filter=insert_mode & default_focussed & prompt_mode("r", "browse") & auto_indentation & preceding_text(r"^\s*$"))
    def _(event):
        text = event.current_buffer.document.text_before_cursor
        textList = text.split("\n")
        if len(textList) >= 2:
            m = re.match(r"^\s*$", textList[-1])
            if m:
                current_indentation = m.group(0)
                previous_indentation = re.match(r"^\s*", textList[-2]).group(0)
                tab_size = event.app.tab_size
                if len(current_indentation) >= event.app.tab_size and \
                        current_indentation == previous_indentation:
                    event.current_buffer.delete_before_cursor(tab_size)

        event.current_buffer.insert_text(event.data)

    @handle('backspace', filter=insert_mode & default_focussed & prompt_mode("r", "browse") & preceding_text(r"^\s+$"))
    def _(event):
        tab_size = event.app.tab_size
        event.current_buffer.delete_before_cursor(tab_size)

    @handle('tab', filter=insert_mode & default_focussed & prompt_mode("r", "browse") & preceding_text(r"^\s*$"))
    def _(event):
        tab_size = event.app.tab_size
        event.current_buffer.insert_text(" " * tab_size)

    # bracketed paste
    @handle(Keys.BracketedPaste, filter=default_focussed & prompt_mode("r", "browse"))
    def _(event):
        data = event.data

        data = data.replace('\r\n', '\n')
        data = data.replace('\r', '\n')

        shouldeval = data[-1] == "\n" and len(event.current_buffer.document.text_after_cursor) == 0
        # todo: allow partial prase complete
        if shouldeval and interface.prase_input_complete(data):
            data = data.rstrip("\n")
            event.current_buffer.insert_text(data)
            event.current_buffer.validate_and_handle()
        else:
            event.current_buffer.insert_text(data)

    # browse mode
    @handle('c-j', filter=insert_mode & default_focussed & prompt_mode("browse") & prase_complete)
    @handle('enter', filter=insert_mode & default_focussed & prompt_mode("browse") & prase_complete)
    def _(event):
        event.current_buffer.validate_and_handle()


    # shell mode
    @handle(
        'backspace',
        filter=insert_mode & default_focussed & prompt_mode("shell") & is_begin_of_buffer,
        save_before=if_no_repeat)
    def _(event):
        event.app.mp.prompt_mode = "r"
        event.app._redraw()

    @handle('c-j', filter=insert_mode & default_focussed & prompt_mode("shell"))
    @handle('enter', filter=insert_mode & default_focussed & prompt_mode("shell"))
    def _(event):
        event.current_buffer.validate_and_handle()

    # readline mode
    @handle('c-j', filter=insert_mode & default_focussed & prompt_mode("readline"))
    @handle('enter', filter=insert_mode & default_focussed & prompt_mode("readline"))
    def _(event):
        event.current_buffer.validate_and_handle()

    # emit completion
    @handle('c-j', filter=insert_mode & default_focussed & app.has_completions)
    @handle('enter', filter=insert_mode & default_focussed & app.has_completions)
    def _(event):
        event.current_buffer.complete_state = None

    # cancle completion
    @handle('c-c', filter=default_focussed & app.has_completions)
    def _(event):
        event.current_buffer.cancel_completion()

    # # tab to completion
    # @handle('tab', filter=insert_mode & default_focussed & app.has_completions & has_complete_index)
    # def _(event):
    #     event.current_buffer.complete_state = None

    return kb
