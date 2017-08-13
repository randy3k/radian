import sys

from .instance import Rinstance
from . import interface
from . import api
from .callbacks import create_read_console, create_write_console_ex
from prompt_toolkit import Prompt
from prompt_toolkit.input import set_default_input
from prompt_toolkit.utils import is_windows


class RoleApplication(object):

    def run(self):

        if not is_windows():
            from prompt_toolkit.input.vt100 import Vt100Input

            class CustomVt100Input(Vt100Input):
                @property
                def responds_to_cpr(self):
                    return False

            terminal_input = CustomVt100Input(sys.stdin)

        p = Prompt(input=terminal_input)

        rinstance = Rinstance()

        def get_text():
            text = None
            while text is None:
                try:
                    text = p.prompt("> ")
                except Exception as e:
                    if isinstance(e, EOFError):
                        # todo: confirmation
                        return None
                    else:
                        raise e
                except KeyboardInterrupt:
                    p.app.future = None

            return text

        def print_text(text, otype):
            print(text)

        rinstance.read_console = create_read_console(get_text)
        rinstance.write_console_ex = create_write_console_ex(print_text)

        # to make api work
        api.rinstance = rinstance

        rinstance.run()
