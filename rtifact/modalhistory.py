from __future__ import unicode_literals
import datetime
import os
from prompt_toolkit.history import History, InMemoryHistory
from prompt_toolkit.application.current import get_app


class ModalInMemoryHistory(InMemoryHistory):

    def __init__(self, include_modes=None, exclude_modes=[]):
        self.strings = []
        self.modes = []
        self.include_modes = include_modes
        self.exclude_modes = exclude_modes

    def append(self, string):
        mode = get_app().mp.prompt_mode
        # don't append to history if this mode is excluced
        if mode in self.exclude_modes:
            return
        # don't append to history if this mode is not included
        if self.include_modes and mode not in self.include_modes:
            return

        self.strings.append(string)
        self.modes.append(mode)


class ModalFileHistory(History):
    """
    :class:`.History` class that stores all strings in a file.
    """
    def __init__(self, filename, include_modes=None, exclude_modes=[]):
        self.strings = []
        self.modes = []
        self.include_modes = include_modes
        self.exclude_modes = exclude_modes
        self.filename = filename
        self._load()

    def _load(self):
        lines = []
        mode = [None]

        def add():
            if lines:
                # Join and drop trailing newline.
                string = ''.join(lines)[:-1]

                self.strings.append(string)
                self.modes.append(mode[0])

        if os.path.exists(self.filename):
            with open(self.filename, 'rb') as f:
                for line in f:
                    line = line.decode('utf-8')

                    if line.startswith('# mode: '):
                        mode[0] = line.replace('# mode: ', '').strip()
                    elif line.startswith('+'):
                        lines.append(line[1:])
                    else:
                        add()
                        mode = [None]
                        lines = []

                add()

    def append(self, string):
        mode = get_app().mp.prompt_mode
        # don't append to history if this mode is excluced
        if mode in self.exclude_modes:
            return
        # don't append to history if this mode is not included
        if self.include_modes and mode not in self.include_modes:
            return

        self.strings.append(string)
        self.modes.append(mode)

        # Save to file.
        with open(self.filename, 'ab') as f:
            def write(t):
                f.write(t.encode('utf-8'))

            write('\n# time: %s UTC' % datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"))
            write('\n# mode: %s\n' % mode)
            for line in string.split('\n'):
                write('+%s\n' % line)

    def __getitem__(self, key):
        return self.strings[key]

    def __iter__(self):
        return iter(self)

    def __len__(self):
        return len(self.strings)
