from __future__ import unicode_literals
from prompt_toolkit.utils import is_windows


if not is_windows():
    from prompt_toolkit.input.vt100 import Vt100Input
    from prompt_toolkit.output.vt100 import Vt100_Output

    class CustomVt100Input(Vt100Input):
        @property
        def responds_to_cpr(self):
            return False

    class CustomVt100Output(Vt100_Output):
        # we don't need buffering
        def write_raw(self, data):
            self.stdout.write(data)

        def write(self, data):
            self.write_raw(data.replace('\x1b', '?'))

        def flush(self):
            self.stdout.flush()
else:
    CustomVt100Input = None
    CustomVt100Output = None
