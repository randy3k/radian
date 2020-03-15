from __future__ import unicode_literals
from prompt_toolkit.utils import is_windows


if not is_windows():
    from prompt_toolkit.input.vt100 import Vt100Input, cooked_mode
    from prompt_toolkit.output.vt100 import Vt100_Output
    import termios

    class rare_mode(cooked_mode):
        @classmethod
        def _patch_lflag(cls, attrs):
            return attrs | (termios.IEXTEN | termios.ISIG)

    class CustomInput(Vt100Input):
        @property
        def responds_to_cpr(self):
            return False

        def rare_mode(self):
            return rare_mode(self.stdin.fileno())

    class CustomOutput(Vt100_Output):
        pass

else:
    from prompt_toolkit.input.win32 import Win32Input, cooked_mode
    from ctypes import windll

    class rare_mode(cooked_mode):
        def _patch(self):
            ENABLE_PROCESSED_INPUT = 0x0001

            windll.kernel32.SetConsoleMode(
                self.handle, self.original_mode.value | ENABLE_PROCESSED_INPUT)

    class CustomInput(Win32Input):
        def rare_mode(self):
            return rare_mode()

    # either Win32Output or Windows10_Output
    CustomOutput = None
