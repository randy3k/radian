from __future__ import unicode_literals
import re

from prompt_toolkit.application.current import get_app

from prompt_toolkit.keys import Keys
from prompt_toolkit.key_binding.key_bindings import KeyBindings
from prompt_toolkit.filters import Condition, has_focus, \
    emacs_insert_mode, vi_insert_mode, in_paste_mode, app
from prompt_toolkit.enums import DEFAULT_BUFFER


default_focussed = has_focus(DEFAULT_BUFFER)
insert_mode = vi_insert_mode | emacs_insert_mode

_prompt_mode_cache = {}


def prompt_mode(mode):
    try:
        return _prompt_mode_cache[mode]
    except KeyError:
        pass
    condition = Condition(lambda: get_app().session.current_mode_name == mode)
    _prompt_mode_cache[mode] = condition
    return condition


_preceding_text_cache = {}
_following_text_cache = {}


def preceding_text(pattern):
    try:
        return _preceding_text_cache[pattern]
    except KeyError:
        pass
    m = re.compile(pattern)

    def _preceding_text():
        app = get_app()
        return bool(m.match(app.current_buffer.document.current_line_before_cursor))

    condition = Condition(_preceding_text)
    _preceding_text_cache[pattern] = condition
    return condition


def following_text(pattern):
    try:
        return _following_text_cache[pattern]
    except KeyError:
        pass
    m = re.compile(pattern)

    def _following_text():
        app = get_app()
        return bool(m.match(app.current_buffer.document.current_line_after_cursor))

    condition = Condition(_following_text)
    _following_text_cache[pattern] = condition
    return condition


@Condition
def cursor_at_begin():
    return get_app().current_buffer.cursor_position == 0


@Condition
def cursor_at_end():
    app = get_app()
    return app.current_buffer.cursor_position == len(app.current_buffer.text)


@Condition
def text_is_empty():
    app = get_app()
    return not app.current_buffer.text


@Condition
def auto_indentation():
    return get_app().session.auto_indentation


@Condition
def auto_match():
    return get_app().session.auto_match


@Condition
def has_complete_index():
    app = get_app()
    cs = app.current_buffer.complete_state
    return cs and cs.complete_index is not None


def if_no_repeat(event):
    return not event.is_repeat


def commit_text(event, text, add_history=True):
    event.app.session.add_history = add_history
    buf = event.current_buffer
    buf.text = text
    buf.validate_and_handle()


def newline(event, chars=["{", "[", "("]):
    should_indent = event.current_buffer.document.char_before_cursor in chars
    copy_margin = not in_paste_mode() and event.app.session.auto_indentation
    event.current_buffer.newline(copy_margin=copy_margin)
    if should_indent and event.app.session.auto_indentation:
        tab_size = event.app.session.tab_size
        event.current_buffer.insert_text(" " * tab_size)


def create_prompt_key_bindings(prase_text_complete):
    kb = KeyBindings()
    handle = kb.add

    @Condition
    def prase_complete():
        app = get_app()
        return prase_text_complete(app.current_buffer.text)

    @handle('c-j', filter=insert_mode & default_focussed)
    @handle('enter', filter=insert_mode & default_focussed)
    def _(event):
        newline(event)

    @handle('c-j', filter=insert_mode & default_focussed & prase_complete)
    @handle('enter', filter=insert_mode & default_focussed & prase_complete)
    def _(event):
        event.current_buffer.validate_and_handle()

    @handle('c-j', filter=insert_mode & default_focussed & auto_match & preceding_text(r".*\{$") & following_text(r"^\}"))
    @handle('enter', filter=insert_mode & default_focussed & auto_match & preceding_text(r".*\{$") & following_text(r"^\}"))
    def _(event):
        copy_margin = not in_paste_mode() and event.app.session.auto_indentation
        event.current_buffer.newline(copy_margin=copy_margin)
        if event.app.session.auto_indentation:
            tab_size = event.app.session.tab_size
            event.current_buffer.insert_text(" " * tab_size)
        event.current_buffer.insert_text("\n")
        event.current_buffer.cursor_position -= 1

    # auto match
    @handle('(', filter=insert_mode & default_focussed & auto_match & following_text(r"[)}\]]|$"))
    def _(event):
        event.current_buffer.insert_text("()")
        event.current_buffer.cursor_left()

    @handle('[', filter=insert_mode & default_focussed & auto_match & following_text(r"[)}\]]|$"))
    def _(event):
        event.current_buffer.insert_text("[]")
        event.current_buffer.cursor_left()

    @handle('{', filter=insert_mode & default_focussed & auto_match & following_text(r"[)}\]]|$"))
    def _(event):
        event.current_buffer.insert_text("{}")
        event.current_buffer.cursor_left()

    @handle('"', filter=insert_mode & default_focussed & auto_match & ~preceding_text(r".*[\"a-zA-Z0-9_]$") & following_text(r"[)}\]]|$"))
    def _(event):
        event.current_buffer.insert_text('""')
        event.current_buffer.cursor_left()

    @handle("'", filter=insert_mode & default_focussed & auto_match & ~preceding_text(r".*['a-zA-Z0-9_]$") & following_text(r"[)}\]]|$"))
    def _(event):
        event.current_buffer.insert_text("''")
        event.current_buffer.cursor_left()

    @handle(')', filter=insert_mode & default_focussed & auto_match & following_text(r"^\)"))
    @handle(']', filter=insert_mode & default_focussed & auto_match & following_text(r"^\]"))
    @handle('}', filter=insert_mode & default_focussed & auto_match & following_text(r"^\}"))
    @handle('"', filter=insert_mode & default_focussed & auto_match & following_text("^\""))
    @handle("'", filter=insert_mode & default_focussed & auto_match & following_text("^'"))
    def _(event):
        event.current_buffer.cursor_right()

    @handle('backspace', filter=insert_mode & default_focussed & auto_match & preceding_text(r".*\($") & following_text(r"^\)"))
    @handle('backspace', filter=insert_mode & default_focussed & auto_match & preceding_text(r".*\[$") & following_text(r"^\]"))
    @handle('backspace', filter=insert_mode & default_focussed & auto_match & preceding_text(r".*\{$") & following_text(r"^\}"))
    @handle('backspace', filter=insert_mode & default_focussed & auto_match & preceding_text('.*"$') & following_text('^"'))
    @handle('backspace', filter=insert_mode & default_focussed & auto_match & preceding_text(r".*'$") & following_text(r"^'"))
    def _(event):
        event.current_buffer.delete()
        event.current_buffer.delete_before_cursor()

    # indentation
    @handle('}', filter=insert_mode & default_focussed & auto_indentation & preceding_text(r"^\s*$"))
    @handle(']', filter=insert_mode & default_focussed & auto_indentation & preceding_text(r"^\s*$"))
    @handle(')', filter=insert_mode & default_focussed & auto_indentation & preceding_text(r"^\s*$"))
    def _(event):
        text = event.current_buffer.document.text_before_cursor
        textList = text.split("\n")
        if len(textList) >= 2:
            m = re.match(r"^\s*$", textList[-1])
            if m:
                current_indentation = m.group(0)
                previous_indentation = re.match(r"^\s*", textList[-2]).group(0)
                tab_size = event.app.session.tab_size
                if len(current_indentation) >= event.app.session.tab_size and \
                        current_indentation == previous_indentation:
                    event.current_buffer.delete_before_cursor(tab_size)

        event.current_buffer.insert_text(event.data)

    @handle('backspace', filter=insert_mode & default_focussed & preceding_text(r"^\s+$"))
    def _(event):
        tab_size = event.app.session.tab_size
        buf = event.current_buffer
        leading_spaces = len(buf.document.text_before_cursor)
        buf.delete_before_cursor(min(tab_size, leading_spaces))

    @handle('tab', filter=insert_mode & default_focussed & preceding_text(r"^\s*$"))
    def _(event):
        tab_size = event.app.session.tab_size
        event.current_buffer.insert_text(" " * tab_size)

    # bracketed paste
    @handle(Keys.BracketedPaste, filter=default_focussed)
    def _(event):
        data = event.data

        data = data.replace('\r\n', '\n')
        data = data.replace('\r', '\n')

        should_eval = data and data[-1] == "\n" and len(event.current_buffer.document.text_after_cursor) == 0
        # todo: allow partial prase complete
        if should_eval and prase_text_complete(data):
            data = data.rstrip("\n")
            event.current_buffer.insert_text(data)
            event.current_buffer.validate_and_handle()
        else:
            event.current_buffer.insert_text(data)

    return kb


# keybinds for both r mond and browse mode
def create_r_key_bindings(prase_text_complete):
    kb = create_prompt_key_bindings(prase_text_complete)
    handle = kb.add

    # r mode
    @handle(';', filter=insert_mode & default_focussed & cursor_at_begin)
    def _(event):
        event.app.session.change_mode("shell")

    return kb


def create_shell_key_bindings():
    kb = KeyBindings()
    handle = kb.add

    # shell mode
    @handle(
        'backspace',
        filter=insert_mode & default_focussed & cursor_at_begin,
        save_before=if_no_repeat)
    def _(event):
        event.app.session.change_mode("r")

    @handle('c-j', filter=insert_mode & default_focussed)
    @handle('enter', filter=insert_mode & default_focussed)
    def _(event):
        event.current_buffer.validate_and_handle()

    return kb


def create_key_bindings():
    kb = KeyBindings()
    handle = kb.add

    # emit completion
    @handle('c-j', filter=insert_mode & default_focussed & app.completion_is_selected)
    @handle('enter', filter=insert_mode & default_focussed & app.completion_is_selected)
    def _(event):
        event.current_buffer.complete_state = None

    # cancel completion
    @handle('c-c', filter=default_focussed & app.has_completions)
    def _(event):
        event.current_buffer.cancel_completion()

    # new line
    @handle('escape', 'enter', filter=emacs_insert_mode)
    def _(event):
        if event.current_buffer.text:
            copy_margin = not in_paste_mode() and event.app.session.auto_indentation
            event.current_buffer.newline(copy_margin=copy_margin)

    return kb


def map_key(key, value, mode="r", filter_str=""):
    import radian
    app = radian.get_app()
    kb = app.session.modes[mode].prompt_key_bindings
    @kb.add(*key, filter=insert_mode & default_focussed, eager=True)
    def _(event):
        event.current_buffer.insert_text(value)
