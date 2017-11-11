from __future__ import unicode_literals
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.application.current import get_app
from prompt_toolkit.search_state import SearchState
from prompt_toolkit.document import Document
from prompt_toolkit.enums import SearchDirection
from contextlib import redirect_stdout


class ModalBuffer(Buffer):
    last_working_index = -1
    last_search_direction = None
    last_search_history = None
    search_history = []

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

    def reset(self, document=None, append_to_history=False):
        self.last_search_history = None
        self.search_history = []
        super().reset(document, append_to_history)

    def history_forward(self, count=1):
        if len(self.text) == 0 and self._is_last_history() and self.last_working_index >= 0:
            self.go_to_history(self.last_working_index)
            self.history_search_text = ""
            self.last_working_index = -1

        super(ModalBuffer, self).history_forward(count)
        self._change_prompt_mode(self.working_index)

    def history_backward(self, count=1):
        super(ModalBuffer, self).history_backward(count)
        self._change_prompt_mode(self.working_index)

    def _search(self, search_state, include_current_position=False, count=1):
        """
        A clone of the original _search function from prompt_toolkit with
        history_search_no_duplicates enhancement.
        """
        assert isinstance(search_state, SearchState)
        assert isinstance(count, int) and count > 0

        text = search_state.text
        direction = search_state.direction
        ignore_case = search_state.ignore_case()

        # modified by rice
        if direction != self.last_search_direction:
            self.last_search_history = None
            self.search_history = []

        # modified by rice
        no_duplicates = get_app().mp.history_search_no_duplicates and count == 1

        def search_once(working_index, document):
            """
            Do search one time.
            Return (working_index, document) or `None`
            """
            if direction == SearchDirection.FORWARD:
                # Try find at the current input.
                new_index = document.find(
                   text, include_current_position=include_current_position,
                   ignore_case=ignore_case)

                if new_index is not None:
                    return (working_index,
                            Document(document.text, document.cursor_position + new_index))
                else:
                    # No match, go forward in the history. (Include len+1 to wrap around.)
                    # (Here we should always include all cursor positions, because
                    # it's a different line.)
                    for i in range(working_index + 1, len(self._working_lines) + 1):
                        i %= len(self._working_lines)

                        # modified by rice
                        if not no_duplicates or self._working_lines[i] not in self.search_history:
                            document = Document(self._working_lines[i], 0)
                            new_index = document.find(text, include_current_position=True,
                                                      ignore_case=ignore_case)
                            if new_index is not None:
                                return (i, Document(document.text, new_index))
            else:
                # Try find at the current input.
                new_index = document.find_backwards(
                    text, ignore_case=ignore_case)

                if new_index is not None:
                    return (working_index,
                            Document(document.text, document.cursor_position + new_index))
                else:
                    # No match, go back in the history. (Include -1 to wrap around.)
                    for i in range(working_index - 1, -2, -1):
                        i %= len(self._working_lines)

                        # modified by rice
                        if not no_duplicates or self._working_lines[i] not in self.search_history:
                            document = Document(self._working_lines[i], len(self._working_lines[i]))
                            new_index = document.find_backwards(
                                text, ignore_case=ignore_case)
                            if new_index is not None:
                                return (i, Document(document.text, len(document.text) + new_index))

        # Do 'count' search iterations.
        working_index = self.working_index
        document = self.document
        for _ in range(count):
            result = search_once(working_index, document)
            if result:
                working_index, document = result

        # modified by rice
        if result:
            working_index, document = result
            self.last_search_direction = direction
            self.last_search_history = self._working_lines[working_index]
            self._change_prompt_mode(result[0], redraw=False)
            return (working_index, document.cursor_position)
        else:
            self.last_search_direction = None
            self.last_search_history = None
            self.search_history = []
            return None

    def apply_search(self, *args, **kwargs):
        super(ModalBuffer, self).apply_search(*args, **kwargs)
        if self.last_search_history and self.last_search_history not in self.search_history:
            self.search_history.append(self.last_search_history)

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
        if app.mp.add_history:
            mode = app.mp.prompt_mode
            if self.text and \
                (not len(self.history) or self.history[-1] != self.text or
                    mode != self.history.modes[-1]):
                self.history.append(self.text)
