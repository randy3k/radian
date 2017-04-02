import time
import os

from prompt_toolkit.shortcuts import \
    create_prompt_application, create_eventloop, CommandLineInterface
from prompt_toolkit.token import Token
from prompt_toolkit.buffer import AcceptAction
from prompt_toolkit.interface import AbortAction
from prompt_toolkit.history import FileHistory

from . import api
from . import interface
from .keybindings import create_key_registry
from .completion import RCompleter


class MultiPrompt(object):
    prompts = {
        "r": "r$> ",
        "help": "help?> ",
        "debug": "debug%> "
    }
    _prompt_mode = "r"

    @property
    def prompt(self):
        return self.prompts[self._prompt_mode]

    @property
    def mode(self):
        return self._prompt_mode

    @mode.setter
    def mode(self, m):
        self._prompt_mode = m


def create_r_eventloop():
    def process_events(context):
        while True:
            if context.input_is_ready():
                break
            api.process_events()
            time.sleep(0.01)
    eventloop = create_eventloop(inputhook=process_events)

    # these are necessary to run the completions in main thread.
    eventloop.run_in_executor = lambda callback: callback()

    return eventloop


class RCommandlineInterface(CommandLineInterface):

    def abort(self):
        # make sure a new line is print
        self._abort_flag = True
        self._redraw()
        self.output.write("\n")
        self.reset()
        self.renderer.request_absolute_cursor_position()
        self.current_buffer.reset(append_to_history=True)


def create_r_repl():
    multi_prompt = MultiPrompt()

    registry = create_key_registry(multi_prompt)

    def get_prompt_tokens(cli):
        return [(Token.Prompt, multi_prompt.prompt)]

    history = FileHistory(os.path.join(os.path.expanduser("~"), ".role_history"))

    application = create_prompt_application(
        get_prompt_tokens=get_prompt_tokens,
        key_bindings_registry=registry,
        multiline=True,
        history=history,
        completer=RCompleter(multi_prompt),
        complete_while_typing=True,
        accept_action=AcceptAction.IGNORE,
        on_exit=AbortAction.RETURN_NONE)

    application.on_start = lambda cli: cli.output.write(interface.r_version() + "\n")

    eventloop = create_r_eventloop()

    return RCommandlineInterface(
            application=application,
            eventloop=eventloop)
