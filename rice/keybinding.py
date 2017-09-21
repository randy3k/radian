from __future__ import unicode_literals
import re
import sys

from prompt_toolkit.application.current import get_app

from prompt_toolkit.keys import Keys
from prompt_toolkit.key_binding.key_bindings import KeyBindings
from prompt_toolkit.key_binding.bindings.named_commands import backward_delete_char
from prompt_toolkit.filters import Condition, has_focus, \
    emacs_insert_mode, vi_insert_mode, in_paste_mode, app
from prompt_toolkit.enums import DEFAULT_BUFFER

from . import api
from . import shell_cmd


def prase_input_complete(text):
    return api.parse_vector(api.mk_string(text))[1] != 2


default_focussed = has_focus(DEFAULT_BUFFER)
insert_mode = vi_insert_mode | emacs_insert_mode


def prompt_mode(mode):
    return Condition(lambda: get_app().mp.prompt_mode == mode)


@Condition
def prase_complete():
    app = get_app()
    return prase_input_complete(app.current_buffer.text)


@Condition
def tab_should_insert_whitespaces():
    app = get_app()
    b = app.current_buffer
    before_cursor = b.document.current_line_before_cursor
    return bool(b.text and (not before_cursor or before_cursor.isspace()))


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


def if_no_repeat(event):
    return not event.is_repeat


def handle_accept(event, append_to_history=True):
    event.current_buffer.last_working_index = event.current_buffer.working_index
    app = get_app()
    app.set_return_value(event.current_buffer.document.text)
    app.pre_run_callables.append(event.current_buffer.reset)
    if append_to_history:
        event.current_buffer.append_to_history()


def create_keybindings():
    kb = KeyBindings()
    handle = kb.add

    # r mode
    @handle(';', filter=insert_mode & default_focussed & prompt_mode("r") & is_begin_of_buffer)
    def _(event):
        event.app.mp.prompt_mode = "shell"
        event.app._redraw()

    @handle('c-j', filter=insert_mode & default_focussed & prompt_mode("r"))
    @handle('enter', filter=insert_mode & default_focussed & prompt_mode("r"))
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
        handle_accept(event)

    # indentation
    @handle('}', filter=insert_mode & default_focussed & prompt_mode("r") & auto_indentation)
    @handle(']', filter=insert_mode & default_focussed & prompt_mode("r") & auto_indentation)
    @handle(')', filter=insert_mode & default_focussed & prompt_mode("r") & auto_indentation)
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

    @handle('backspace', filter=insert_mode & default_focussed & prompt_mode("r"))
    def _(event):
        document = event.current_buffer.document
        text = document.current_line_before_cursor
        tab_size = event.app.tab_size
        if text.endswith(" " * tab_size) and len(text.strip()) == 0 and event.arg == 1:
            event.current_buffer.delete_before_cursor(tab_size)
        else:
            backward_delete_char(event)

    @handle('tab', filter=insert_mode & default_focussed & prompt_mode("r") & tab_should_insert_whitespaces)
    def _(event):
        tab_size = event.app.tab_size
        event.current_buffer.insert_text(" " * tab_size)

    # bracketed paste
    @handle(Keys.BracketedPaste, filter=default_focussed & prompt_mode("r"))
    def _(event):
        data = event.data

        data = data.replace('\r\n', '\n')
        data = data.replace('\r', '\n')

        shouldeval = data[-1] == "\n" and len(event.current_buffer.document.text_after_cursor) == 0
        # todo: allow partial prase complete
        if shouldeval and prase_input_complete(data):
            data = data.rstrip("\n")
            event.current_buffer.insert_text(data)
            handle_accept(event)
        else:
            event.current_buffer.insert_text(data)

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
        event.current_buffer.last_working_index = event.current_buffer.working_index
        sys.stdout.write("\n")
        event.current_buffer.append_to_history()
        shell_cmd.run_shell_command(event.current_buffer.text)
        event.current_buffer.reset()

    # readline mode
    @handle('c-j', filter=insert_mode & default_focussed & prompt_mode("readline"))
    @handle('enter', filter=insert_mode & default_focussed & prompt_mode("readline"))
    def _(event):
        handle_accept(event, append_to_history=False)

    handle('up', filter=prompt_mode("readline"))(lambda event: None)
    handle('down', filter=prompt_mode("readline"))(lambda event: None)

    # emit completion
    @handle('c-j', filter=insert_mode & default_focussed & app.has_completions)
    @handle('enter', filter=insert_mode & default_focussed & app.has_completions)
    def _(event):
        event.current_buffer.complete_state = None

    # cancle completion
    @handle('escape', 'escape', filter=insert_mode & default_focussed & app.has_completions)
    def _(event):
        event.current_buffer.cancel_completion()

    return kb
