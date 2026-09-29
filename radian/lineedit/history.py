import datetime
import os
from prompt_toolkit.history import History


class ModalHistory(History):
    def _ensure_loaded(self):
        if not self._loaded:
            self._loaded_strings = list(self.load_history_strings())
            self._loaded = True

    def load(self):
        self._ensure_loaded()
        yield from self._loaded_strings

    def append_string(self, string: str, mode=None) -> None:
        self._ensure_loaded()
        self._loaded_strings.insert(0, (mode, string))
        self.store_string(string, mode)

    def get_strings(self):
        self._ensure_loaded()
        return [s for _, s in reversed(self._loaded_strings)]

    def get_modes(self):
        self._ensure_loaded()
        return [m for m, _ in reversed(self._loaded_strings)]


class ModalInMemoryHistory(ModalHistory):
    def load_history_strings(self):
        return []

    def store_string(self, string, mode=None):
        pass


class ModalFileHistory(ModalHistory):
    def __init__(self, filename, max_history_size):
        self.filename = filename
        self.max_history_size = max_history_size
        super().__init__()

    def load_history_strings(self):
        strings = []
        lines = []
        mode = None
        entry_starts = []

        def add() -> None:
            # Join and drop trailing newline.
            strings.append((mode, "".join(lines)[:-1]))
            entry_starts.append(entry_start)

        if os.path.exists(self.filename):
            with open(self.filename, "rb") as f:
                raw_lines = f.readlines()

            entry_start = 0
            for i, line_bytes in enumerate(raw_lines):
                line = line_bytes.decode("utf-8", errors="replace")

                if line.startswith("+"):
                    lines.append(line[1:])
                else:
                    if lines:
                        add()
                        lines = []
                        mode = None
                        entry_start = i
                    if line.startswith("# mode: "):
                        mode = line[8:].strip()

            if lines:
                add()

            max_size = max(self.max_history_size, 10)
            if len(strings) > max_size:
                # trim history if it is too big
                keep = round(max_size * 0.9)
                strings = strings[-keep:]
                trimmed = raw_lines[entry_starts[-keep]:]
                with open(self.filename, "wb") as f:
                    f.writelines(trimmed)

        # Reverse the order, because newest items have to go first.
        return reversed(strings)

    def store_string(self, string, mode):
        with open(self.filename, "ab") as f:
            def write(t):
                f.write(t.encode("utf-8"))

            now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            write(f"\n# time: {now} UTC")
            write(f"\n# mode: {mode}\n")
            for line in string.split("\n"):
                write(f"+{line}\n")
