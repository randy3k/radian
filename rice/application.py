import sys
import os
import time

from .instance import Rinstance
from . import interface
from . import api
from .callbacks import create_read_console, create_write_console_ex
from prompt_toolkit import Prompt
from prompt_toolkit.application.current import get_app
from prompt_toolkit.input import set_default_input
from prompt_toolkit.eventloop import create_event_loop, set_event_loop

from prompt_toolkit.utils import is_windows
from prompt_toolkit.layout.lexers import PygmentsLexer
from pygments.lexers.r import SLexer, RConsoleLexer
from prompt_toolkit.styles import default_style, merge_styles, style_from_pygments
from pygments.styles import get_style_by_name
from prompt_toolkit.history import FileHistory
from prompt_toolkit.layout.processors import HighlightMatchingBracketProcessor
from prompt_toolkit.key_binding.key_bindings import KeyBindings, ConditionalKeyBindings
from prompt_toolkit.filters import is_done, has_focus, to_filter, Condition
from prompt_toolkit.enums import DEFAULT_BUFFER, SEARCH_BUFFER
from prompt_toolkit.formatted_text import ANSI


from .completion import RCompleter


class MultiPrompt(Prompt):
    _prompts = {
        "r": ANSI("\x1b[34mr$>\x1b[0m "),
        "help": ANSI("\x1b[33mhelp?>\x1b[0m "),
        "help_search": ANSI("\x1b[33mhelp??>\x1b[0m "),
        "debug": "debug%> "
    }
    _default_prompt_mode = "r"

    def __init__(self, *args, **kwargs):
        super(MultiPrompt, self).__init__(*args, **kwargs)
        self.app.prompt_mode = self._default_prompt_mode

    def prompt(self, **kwargs):
        message = self._prompts[self.app.prompt_mode]
        return super(MultiPrompt, self).prompt(message, **kwargs)

if not is_windows():
    from prompt_toolkit.input.vt100 import Vt100Input

    class CustomVt100Input(Vt100Input):
        @property
        def responds_to_cpr(self):
            return False


def printer(text, otype=0):
    if otype == 0:
        sys.stdout.write(text)
    else:
        sys.stderr.write(text)


def prase_input_complete(app):
    return api.parse_vector(api.mk_string(app.current_buffer.text))[1] != 2


def create_multi_prompt():

    history = FileHistory(os.path.join(os.path.expanduser("~"), ".role_history"))
    vt100 = CustomVt100Input(sys.stdin)

    def process_events(context):
        while True:
            if context.input_is_ready():
                break
            api.process_events()
            time.sleep(1.0/30)

    set_event_loop(create_event_loop(inputhook=process_events))

    rcompleter = RCompleter()

    style = merge_styles([
        default_style(),
        style_from_pygments(get_style_by_name("vim"))])

    kb = KeyBindings()

    @Condition
    def do_accept():
        app = get_app()
        if app.current_buffer.name != DEFAULT_BUFFER or not prase_input_complete(app):
            return False

        return True

    @kb.add('enter', filter=do_accept)
    def _(event):
        event.app.current_buffer.validate_and_handle()

    @kb.add('c-c')
    def _(event):
        event.app.abort()

    p = MultiPrompt(
        multiline=True,
        complete_while_typing=True,
        enable_suspend=True,
        lexer=PygmentsLexer(SLexer),
        style=style,
        completer=rcompleter,
        history=history,
        extra_key_bindings=kb,
        extra_input_processor=HighlightMatchingBracketProcessor(),
        input=vt100 if not is_windows() else None
    )

    def on_render(app):
        if app.is_aborting:
            printer("\n")

    p.app.on_render += on_render

    return p


class RiceApplication(object):

    def run(self):
        p = create_multi_prompt()

        rinstance = Rinstance()

        _first_time = [True]

        def result_from_prompt():
            if _first_time[0]:
                printer(interface.r_version(), 0)
                _first_time[0] = False

            printer("\n")
            text = None
            while text is None:
                try:
                    text = p.prompt()
                except Exception as e:
                    if isinstance(e, EOFError):
                        # todo: confirmation
                        return None
                    else:
                        raise e
                except KeyboardInterrupt:
                    pass

            return text

        rinstance.read_console = create_read_console(result_from_prompt)
        rinstance.write_console_ex = create_write_console_ex(printer)

        # to make api work
        api.rinstance = rinstance

        rinstance.run()
