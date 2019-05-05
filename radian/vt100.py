from __future__ import unicode_literals
from prompt_toolkit.application.current import get_app
from prompt_toolkit.utils import is_windows
import errno

if not is_windows():
    from prompt_toolkit.input.vt100 import Vt100Input
    from prompt_toolkit.output.vt100 import Vt100_Output

    class CustomVt100Input(Vt100Input):
        @property
        def responds_to_cpr(self):
            return False

    class CustomVt100Output(Vt100_Output):

        def flush(self):
            # it is needed when the stdout was redirected
            # see https://github.com/Non-Contradiction/JuliaCall/issues/39
            try:
                if self._buffer:
                    data = ''.join(self._buffer)
                    if self.write_binary:
                        if hasattr(self.stdout, 'buffer'):
                            out = self.stdout.buffer  # Py3.
                        else:
                            out = self.stdout
                        out.write(data.encode(self.stdout.encoding or 'utf-8', 'replace'))
                    else:
                        self.stdout.write(data)
                    self._buffer = []
            except IOError as e:
                if e.args and e.args[0] == errno.EINTR:
                    pass
                elif e.args and e.args[0] == 0:
                    pass
                else:
                    raise
            try:
                self.stdout.flush()
            except IOError as e:
                if e.args and e.args[0] == errno.EAGAIN:
                    app = get_app()
                    app.renderer.render(app, app.layout)
                    pass
                else:
                    raise
else:

    class CustomVt100Input(object):
        pass

    class CustomVt100Output(object):
        pass
