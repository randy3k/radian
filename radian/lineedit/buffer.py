from prompt_toolkit.application.current import get_app
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.search import SearchState, SearchDirection
from prompt_toolkit.document import Document

from collections import deque
import logging

logger = logging.getLogger(__name__)


class BetterBuffer(Buffer):
    def __init__(self, *args, search_no_duplicates, **kwargs):
        self.search_no_duplicates = search_no_duplicates

        self._last_working_index = -1

        self._in_search = False
        self._last_search_direction = None
        self._last_search_history = None
        self._search_history = []
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

    def _search_matches(self, i):
        no_duplicates = self.search_no_duplicates
        return not no_duplicates or self._working_lines[i] not in self._search_history

    def _search(
        self,
        search_state: SearchState,
        include_current_position: bool = False,
        count: int = 1):
        # modified to support search_no_duplicates

        assert count > 0

        text = search_state.text
        direction = search_state.direction
        ignore_case = search_state.ignore_case()

        # added by radian
        if direction != self._last_search_direction:
            self._last_search_history = None
            self._search_history = []

        self._in_search = True

        def search_once(
            working_index: int, document: Document
        ):
            """
            Do search one time.
            Return (working_index, document) or `None`
            """
            if direction == SearchDirection.FORWARD:
                # Try find at the current input.
                new_index = document.find(
                    text,
                    include_current_position=include_current_position,
                    ignore_case=ignore_case,
                )

                if new_index is not None:
                    return (
                        working_index,
                        Document(document.text, document.cursor_position + new_index),
                    )
                else:
                    # No match, go forward in the history. (Include len+1 to wrap around.)
                    # (Here we should always include all cursor positions, because
                    # it's a different line.)
                    for i in range(working_index + 1, len(self._working_lines) + 1):
                        i %= len(self._working_lines)

                        # modified by radian
                        if self._search_matches(i):
                            document = Document(self._working_lines[i], 0)
                            new_index = document.find(text, include_current_position=True,
                                                      ignore_case=ignore_case)
                            if new_index is not None:
                                return (i, Document(document.text, new_index))
            else:
                # Try find at the current input.
                new_index = document.find_backwards(text, ignore_case=ignore_case)

                if new_index is not None:
                    return (
                        working_index,
                        Document(document.text, document.cursor_position + new_index),
                    )
                else:
                    # No match, go back in the history. (Include -1 to wrap around.)
                    for i in range(working_index - 1, -2, -1):
                        i %= len(self._working_lines)

                        # modified by radian
                        if self._search_matches(i):
                            document = Document(self._working_lines[i], len(self._working_lines[i]))
                            new_index = document.find_backwards(
                                text, ignore_case=ignore_case)
                            if new_index is not None:
                                return (i, Document(document.text, len(document.text) + new_index))
            return None

        # modified by radian
        working_index = self.working_index
        document = self.document
        for _ in range(count):
            result = search_once(working_index, document)
            if result:
                working_index, document = result

        if result:
            working_index, document = result
            self._last_search_direction = direction
            self._last_search_history = self._working_lines[working_index]
            return (working_index, document.cursor_position)
        else:
            self._last_search_direction = None
            self._last_search_history = None
            self._search_history = []
            return None

    def apply_search(self, *args, **kwargs):
        super().apply_search(*args, **kwargs)
        if self._last_search_history and self._last_search_history not in self._search_history:
            self._search_history.append(self._last_search_history)
        self._in_search = False

    def go_to_next_history(self, i):
        self.go_to_history(i)
        self.history_search_text = ""
        self.history_forward()
        self.cursor_position = len(self.text)

    def auto_up(self, *args, **kwargs):
        if not self.complete_state and not self.selection_state and \
                not self._is_last_history() and self._is_end_of_buffer():
            self.history_backward()
            self.cursor_position = len(self.text)
        else:
            super().auto_up(*args, **kwargs)

    def auto_down(self, *args, **kwargs):
        if not self.complete_state and not self.selection_state and \
                not self._is_last_history() and self._is_end_of_buffer():
            self.history_forward()
            self.cursor_position = len(self.text)
        elif not self.complete_state and not self.selection_state and \
                self._is_last_history() and len(self.text) == 0 and self._last_working_index >= 0 \
                and self._last_working_index < len(self._working_lines) - 1:
            # down arrow after commiting a history line
            self.go_to_next_history(self._last_working_index)
            self._last_working_index = -1
        else:
            super().auto_down(*args, **kwargs)

    def _reset_searching(self):
        self._in_search = False
        self._last_search_direction = None
        self._last_search_history = None
        self._search_history = []

    def reset(self, *args, **kwargs):
        self._reset_searching()
        super().reset(*args, **kwargs)


class ModalBuffer(BetterBuffer):
    def __init__(self, *args, session, **kwargs):
        self.session = session
        super().__init__(*args, **kwargs)
        # we don't use load_history_if_not_yet_loaded because it breaks ctrl-o
        # https://github.com/prompt-toolkit/python-prompt-toolkit
        self._reset_history()

    # def _set_working_mode(self):
    #     if not self._in_search and self._is_last_history():
    #         self.working_mode = self.session.current_mode

    # def _change_working_mode(self, index):
    #     if index < len(self._working_lines_mode) - 1:
    #         mode = self._working_lines_mode[index]
    #         self.session.activate_mode(mode)
    #     elif self.working_mode:
    #         self.session.activate_mode(self.working_mode)

    def _history_mode_matches(self, i):
        if i == len(self._working_lines) - 1:
            return True
        else:
            spec = self.session.current_mode_spec
            next_mode = self._working_lines_mode[i]
            if next_mode == spec.name:
                return True
            elif next_mode in self.session.specs and \
                    spec.history_book == self.session.specs[next_mode].history_book:
                return True
        return False

    def _history_matches(self, i):
        return super()._history_matches(i) and self._history_mode_matches(i)

    def load_history_if_not_yet_loaded(self):
        # use _reset_history instead
        pass

    def _search_matches(self, i):
        return super()._search_matches(i) and self._history_mode_matches(i)

    def _search(self, *args, **kwargs):
        # self._set_working_mode()
        res = super()._search(*args, **kwargs)
        # if res:
        #     self._change_working_mode(res[0])
        return res

    def auto_up(self, *args, **kwargs):
        # self._set_working_mode()
        super().auto_up(*args, **kwargs)
        # self._change_working_mode(self.working_index)

    def auto_down(self, *args, **kwargs):
        # self._set_working_mode()
        super().auto_down(*args, **kwargs)
        # self._change_working_mode(self.working_index)

    def append_to_history(self) -> None:
        if not self.session.add_history:
            return
        if not self.session.current_mode_spec.keep_history:
            return
        if self.text:
            history_strings = self.history.get_strings()
            history_modes = self.history.get_modes()
            if not len(history_strings) or \
                    history_strings[-1] != self.text or \
                    history_modes[-1] != self.session.current_mode:
                self.history.append_string(self.text, self.session.current_mode)

    def _reset_history(self):
        self._working_lines_mode = deque([None])
        self.working_mode = None
        for m, item in self.history.load():
            self._working_lines.appendleft(item)
            self._working_lines_mode.appendleft(m)
            self._Buffer__working_index += 1

    def reset(self, *args, **kwargs):
        super().reset(*args, **kwargs)
        self._reset_history()
