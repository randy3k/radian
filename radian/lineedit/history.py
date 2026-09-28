import datetime
import os
from prompt_toolkit.history import InMemoryHistory, FileHistory


class ModelHistory:
    def load(self):
        if not self._loaded:
            self._loaded_strings = list(self.load_history_strings())
            self._loaded = True

        for item in self._loaded_strings:
            yield item

    def append_string(self, string: str, mode) -> None:
        self._loaded_strings.insert(0, (mode, string))
        self.store_string(string, mode)

    def get_strings(self):
        return [s for _, s in reversed(self._loaded_strings)]

    def get_modes(self):
        return [m for m, _ in reversed(self._loaded_strings)]


class ModalInMemoryHistory(ModelHistory, InMemoryHistory):
    def store_string(self, string, mode):
        pass


class ModalFileHistory(ModelHistory, FileHistory):
    def __init__(self, history_file, max_history_size):
        self.max_history_size = max_history_size
        super().__init__(history_file)

    def load_history_strings(self):
        strings = []
        lines = []
        mode = [None]
        entry_starts = []

        def add() -> None:
            if lines:
                # Join and drop trailing newline.
                string = (mode[0], "".join(lines)[:-1])
                strings.append(string)

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
                        entry_starts.append(entry_start)
                        lines = []
                        mode[0] = None
                        entry_start = i
                    if line.startswith('# mode: '):
                        mode[0] = line[8:].strip()

            if lines:
                add()
                entry_starts.append(entry_start)

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
        # Save to file.
        with open(self.filename, 'ab') as f:
            def write(t):
                f.write(t.encode('utf-8'))

            write('\n# time: %s UTC' % datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S"))
            write('\n# mode: %s\n' % mode)
            for line in string.split('\n'):
                write('+%s\n' % line)
