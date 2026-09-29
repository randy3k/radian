from collections import deque

from prompt_toolkit.buffer import Buffer
from prompt_toolkit.search import SearchState


class ModalBuffer(Buffer):
    def __init__(self, *args, session, **kwargs):
        self.session = session
        self._last_working_index = -1
        self._last_search_direction = None
        self._last_search_history = None
        self._search_history = set()

        # Note: super().__init__ calls self.reset(), which calls _reset_history().
        # We override load_history_if_not_yet_loaded to a no-op and load history
        # synchronously in _reset_history() because async history loading breaks ctrl-o.
        super().__init__(*args, **kwargs)

        original_accept_handler = self.accept_handler

        def _handler(*args, **kwargs):
            self._last_working_index = self.working_index
            return original_accept_handler(*args, **kwargs)

        self.accept_handler = _handler

    def _is_end_of_buffer(self):
        return self.cursor_position == len(self.text)

    def _is_last_history(self):
        return self.working_index == len(self._working_lines) - 1

    def _history_mode_matches(self, i):
        if i == len(self._working_lines) - 1:
            return True
        mode = self.session.modes.get(self._working_lines_mode[i])
        return (
            mode is not None
            and mode.history_book == self.session.current_mode.history_book
        )

    def _history_matches(self, i):
        return super()._history_matches(i) and self._history_mode_matches(i)

    def _search_matches(self, i):
        return (
            not self.session.search_no_duplicates
            or self._working_lines[i] not in self._search_history
        ) and self._history_mode_matches(i)

    def load_history_if_not_yet_loaded(self):
        # use _reset_history instead
        pass

    def _search(
        self,
        search_state: SearchState,
        include_current_position: bool = False,
        count: int = 1,
    ):
        if search_state.direction != self._last_search_direction:
            self._reset_searching()
        if not search_state.text:
            self._reset_searching()
            return (self.working_index, self.cursor_position)

        orig_lines = self._working_lines
        self._working_lines = [
            line if i == self.working_index or self._search_matches(i) else ""
            for i, line in enumerate(orig_lines)
        ]
        try:
            result = super()._search(
                search_state,
                include_current_position=include_current_position,
                count=count,
            )
        finally:
            self._working_lines = orig_lines

        if result is None or (
            not include_current_position
            and result == (self.working_index, self.cursor_position)
            and not self._search_matches(result[0])
        ):
            self._last_search_history = None
            return None

        self._last_search_direction = search_state.direction
        self._last_search_history = self._working_lines[result[0]]
        return result

    def apply_search(
        self,
        search_state: SearchState,
        include_current_position: bool = True,
        count: int = 1,
    ):
        if not include_current_position and not self._is_last_history():
            self._search_history.add(self.text)
        super().apply_search(
            search_state,
            include_current_position=include_current_position,
            count=count,
        )
        if include_current_position:
            self._reset_searching()
        elif self._last_search_history:
            self._search_history.add(self._last_search_history)

    def go_to_next_history(self, i):
        self.go_to_history(i)
        self.history_search_text = ""
        self.history_forward()
        self.cursor_position = len(self.text)

    def auto_up(self, *args, **kwargs):
        if (
            not self.complete_state
            and not self.selection_state
            and not self._is_last_history()
            and self._is_end_of_buffer()
        ):
            self.history_backward()
            self.cursor_position = len(self.text)
        else:
            super().auto_up(*args, **kwargs)

    def auto_down(self, *args, **kwargs):
        if (
            not self.complete_state
            and not self.selection_state
            and not self._is_last_history()
            and self._is_end_of_buffer()
        ):
            self.history_forward()
            self.cursor_position = len(self.text)
        elif (
            not self.complete_state
            and not self.selection_state
            and self._is_last_history()
            and len(self.text) == 0
            and 0 <= self._last_working_index < len(self._working_lines) - 1
        ):
            # down arrow after committing a history line
            self.go_to_next_history(self._last_working_index)
            self._last_working_index = -1
        else:
            super().auto_down(*args, **kwargs)

    def append_to_history(self) -> None:
        if not self.session.add_history or not self.text:
            return
        keep = self.session.current_mode.keep_history
        if not (keep(self.text) if callable(keep) else keep):
            return
        self.history._ensure_loaded()
        loaded = self.history._loaded_strings
        if not loaded or loaded[0] != (self.session.current_mode.name, self.text):
            self.history.append_string(self.text, self.session.current_mode.name)

    def _reset_searching(self):
        self._last_search_direction = None
        self._last_search_history = None
        self._search_history.clear()

    def _reset_history(self):
        self._working_lines_mode = deque([None])
        for m, item in self.history.load():
            self._working_lines.appendleft(item)
            self._working_lines_mode.appendleft(m)
            self._Buffer__working_index += 1

    def reset(self, *args, **kwargs):
        self._reset_searching()
        super().reset(*args, **kwargs)
        self._reset_history()
