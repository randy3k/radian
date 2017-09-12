from __future__ import unicode_literals
import re

from prompt_toolkit.application.current import get_app

from prompt_toolkit.keys import Keys
from prompt_toolkit.key_binding.key_bindings import KeyBindings
from prompt_toolkit.filters import Condition
from prompt_toolkit.filters import emacs_insert_mode, vi_insert_mode, in_paste_mode
from prompt_toolkit.enums import DEFAULT_BUFFER

from . import api


def prase_input_complete(text):
    return api.parse_vector(api.mk_string(text))[1] != 2


def create_keybindings():
    kb = KeyBindings()

    @Condition
    def prase_complete():
        app = get_app()
        return prase_input_complete(app.current_buffer.text)

    @Condition
    def is_completing():
        app = get_app()
        return app.current_buffer.complete_state

    @Condition
    def is_default_buffer():
        app = get_app()
        return app.current_buffer.name == DEFAULT_BUFFER

    @Condition
    def tab_should_insert_whitespaces():
        app = get_app()
        b = app.current_buffer
        before_cursor = b.document.current_line_before_cursor
        return bool(b.text and (not before_cursor or before_cursor.isspace()))

    @Condition
    def is_begining_of_buffer():
        return get_app().current_buffer.cursor_position == 0

    @Condition
    def is_end_of_buffer():
        app = get_app()
        return app.current_buffer.cursor_position == len(app.current_buffer.text)

    @Condition
    def is_empty():
        return len(get_app().current_buffer.text) == 0

    @Condition
    def last_history():
        app = get_app()
        return app.current_buffer.working_index == len(app.current_buffer._working_lines) - 1

    insert_mode = vi_insert_mode | emacs_insert_mode

    last_working_index = [-1]

    @kb.add(Keys.ControlJ, filter=insert_mode & is_default_buffer)
    @kb.add('enter', filter=insert_mode & is_default_buffer)
    def _(event):
        if event.current_buffer.document.char_before_cursor in ["{", "[", "("]:
            event.current_buffer.newline(copy_margin=not in_paste_mode())
            event.current_buffer.insert_text('    ')
        else:
            event.current_buffer.newline(copy_margin=not in_paste_mode())

    @kb.add(Keys.ControlJ, filter=insert_mode & is_default_buffer & prase_complete)
    @kb.add('enter', filter=insert_mode & is_default_buffer & prase_complete)
    def _(event):
        last_working_index[0] = event.current_buffer.working_index
        event.current_buffer.validate_and_handle()

    @kb.add(Keys.ControlJ, filter=insert_mode & is_default_buffer & is_completing)
    @kb.add('enter', filter=insert_mode & is_default_buffer & prase_complete & is_completing)
    def _(event):
        event.current_buffer.complete_state = None

    @kb.add(Keys.BracketedPaste, filter=is_default_buffer)
    def _(event):
        data = event.data

        data = data.replace('\r\n', '\n')
        data = data.replace('\r', '\n')

        shouldeval = data[-1] == "\n" and len(event.current_buffer.document.text_after_cursor) == 0
        # todo: allow partial prase complete
        if shouldeval and prase_input_complete(data):
            data = data.rstrip("\n")
            event.current_buffer.insert_text(data)
            event.current_buffer.validate_and_handle()
        else:
            event.current_buffer.insert_text(data)

    # indentation

    @kb.add('}', filter=insert_mode & is_default_buffer)
    @kb.add(']', filter=insert_mode & is_default_buffer)
    @kb.add(')', filter=insert_mode & is_default_buffer)
    def _(event):
        text = event.current_buffer.document.text_before_cursor
        textList = text.split("\n")
        if len(textList) >= 2:
            m = re.match(r"^\s*$", textList[-1])
            if m:
                current_indentation = m.group(0)
                previous_indentation = re.match(r"^\s*", textList[-2]).group(0)
                if len(current_indentation) >= 4 and current_indentation == previous_indentation:
                    event.current_buffer.delete_before_cursor(4)

        event.current_buffer.insert_text(event.data)

    @kb.add(Keys.Tab, filter=insert_mode & is_default_buffer & tab_should_insert_whitespaces)
    def _(event):
        event.current_buffer.insert_text('    ')

    # history

    @kb.add(Keys.Up, filter=is_default_buffer & is_end_of_buffer & ~last_history)
    def _(event):
        event.current_buffer.history_backward(count=event.arg)
        event.current_buffer.cursor_position = len(event.current_buffer.text)

    @kb.add(Keys.Down, filter=is_default_buffer & is_end_of_buffer & ~last_history)
    def _(event):
        event.current_buffer.history_forward(count=event.arg)
        event.current_buffer.cursor_position = len(event.current_buffer.text)

    @kb.add(Keys.Down, filter=is_default_buffer & is_empty & last_history)
    def _(event):
        if last_working_index[0] >= 0:
            event.current_buffer.go_to_history(last_working_index[0] + 1)
            last_working_index[0] = -1

    return kb
