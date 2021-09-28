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
    def load_history_strings(self):
        strings = []
        lines = []
        mode = [None]

        def add() -> None:
            if lines:
                # Join and drop trailing newline.
                string = (mode[0], "".join(lines)[:-1])
                strings.append(string)

        if os.path.exists(self.filename):
            with open(self.filename, "rb") as f:
                for line_bytes in f:
                    line = line_bytes.decode("utf-8", errors="replace")

                    if line.startswith('# mode: '):
                        mode[0] = line.replace('# mode: ', '').strip()
                    elif line.startswith("+"):
                        lines.append(line[1:])
                    else:
                        add()
                        lines = []

                add()

        # Reverse the order, because newest items have to go first.
        return reversed(strings)

    def store_string(self, string, mode):
        # Save to file.
        with open(self.filename, 'ab') as f:
            def write(t):
                f.write(t.encode('utf-8'))

            write('\n# time: %s UTC' % datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"))
            write('\n# mode: %s\n' % mode)
            for line in string.split('\n'):
                write('+%s\n' % line)
