from __future__ import unicode_literals
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.application.current import get_app


class ModalBuffer(Buffer):
    last_working_index = -1

    def _change_prompt_mode(self, index, redraw=True):
        if index < len(self.history.modes):
            app = get_app()
            if app.mp.prompt_mode in app.mp.top_level_modes:
                mode = self.history.modes[index]
                if mode and mode in app.mp.top_level_modes:
                    app.mp.prompt_mode = mode
                    if redraw:
                        app._redraw()

    def _is_end_of_buffer(self):
        return self.cursor_position == len(self.text)

    def _is_last_history(self):
        return self.working_index == len(self._working_lines) - 1

    def history_forward(self, count=1):
        if len(self.text) == 0 and self._is_last_history() and self.last_working_index >= 0:
            self.go_to_history(self.last_working_index)
            self.last_working_index = -1

        super(ModalBuffer, self).history_forward(count)
        self._change_prompt_mode(self.working_index)

    def history_backward(self, count=1):
        super(ModalBuffer, self).history_backward(count)
        self._change_prompt_mode(self.working_index)

    def _search(self, *args, **kwargs):
        result = super(ModalBuffer, self)._search(*args, **kwargs)
        if result:
            self._change_prompt_mode(result[0], redraw=False)
        return result

    def apply_search(self, *args, **kwargs):
        super(ModalBuffer, self).apply_search(*args, **kwargs)
        self._change_prompt_mode(self.working_index)

    def auto_up(self, count=1, go_to_start_of_line_if_history_changes=False):
        if not self._is_last_history() and self._is_end_of_buffer():
            self.history_backward()
            self.cursor_position = len(self.text)
        else:
            super(ModalBuffer, self).auto_up(count, go_to_start_of_line_if_history_changes)

    def auto_down(self, count=1, go_to_start_of_line_if_history_changes=False):
        if not self._is_last_history() and self._is_end_of_buffer():
            self.history_forward()
            self.cursor_position = len(self.text)
        else:
            super(ModalBuffer, self).auto_down(count, go_to_start_of_line_if_history_changes)

    def append_to_history(self):
        app = get_app()
        mode = app.mp.prompt_mode
        if self.text and \
            (not len(self.history) or self.history[-1] != self.text or
                mode != self.history.modes[-1]):
            self.history.append(self.text)
