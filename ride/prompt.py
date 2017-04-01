from __future__ import unicode_literals
from prompt_toolkit.shortcuts import \
    create_prompt_application, create_eventloop, CommandLineInterface
from prompt_toolkit.token import Token
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.key_binding.defaults import load_key_bindings_for_prompt
from prompt_toolkit.keys import Keys
from prompt_toolkit.filters import Condition
from prompt_toolkit.buffer import AcceptAction
from prompt_toolkit.interface import AbortAction
from prompt_toolkit.history import FileHistory
import time
import os
import traceback

from .runtime import Rinstance
from . import api
from . import interface


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


class RCompleter(Completer):

    def __init__(self, multi_prompt):
        self.multi_prompt = multi_prompt
        self.assignLinebuffer = self.get_utils_func(".assignLinebuffer")
        self.assignEnd = self.get_utils_func(".assignEnd")
        self.guessTokenFromLine = self.get_utils_func(".guessTokenFromLine")
        self.completeToken = self.get_utils_func(".completeToken")
        self.retrieveCompletions = self.get_utils_func(".retrieveCompletions")

    def get_utils_func(self, fname):
        f = interface.rlang(api.mk_symbol(":::"), api.mk_string("utils"), api.mk_string(fname))
        api.preserve_object(f)
        return f

    def get_completions(self, document, complete_event):
        completions = []
        token = ""
        if self.multi_prompt.mode in ["r", "help"]:
            text = document.text
            s = api.protect(api.mk_string(text))
            interface.rcall(self.assignLinebuffer, s)
            interface.rcall(self.assignEnd, api.scalar_integer(len(text)))
            token = interface.rcopy(interface.rcall(self.guessTokenFromLine))[0]
            if (len(token) > 3 and text[-1].isalnum()) or complete_event.completion_requested:
                interface.rcall(self.completeToken)
                completions = interface.rcopy(interface.rcall(self.retrieveCompletions))
            api.unprotect(1)
        for c in completions:
            yield Completion(c, -len(token))


def create_key_registry(multi_prompt):
    registry = load_key_bindings_for_prompt(enable_system_bindings=True)

    is_begining_of_line = Condition(lambda cli: cli.current_buffer.cursor_position == 0)

    @Condition
    def prase_complete(cli):
        return api.parse_vector(api.mk_string(cli.current_buffer.text))[1] != 2

    is_returnable = Condition(lambda cli: cli.current_buffer.accept_action.is_returnable)

    def in_prompt_mode(m):
        return Condition(lambda _: multi_prompt.mode == m)

    # R prompt

    @registry.add_binding(Keys.ControlJ, filter=prase_complete & in_prompt_mode("r") & is_returnable)
    def _(event):
        buff = event.current_buffer
        buff.accept_action.validate_and_handle(event.cli, buff)

    @registry.add_binding("?", filter=is_begining_of_line & in_prompt_mode("r"))
    def _(event):
        multi_prompt.mode = "help"

    @registry.add_binding(Keys.ControlP, filter=in_prompt_mode("r"))
    def _(event):
        multi_prompt.mode = "debug"

    # help prompt

    @registry.add_binding(Keys.Backspace, filter=is_begining_of_line & in_prompt_mode("help"))
    def _(event):
        multi_prompt.mode = "r"

    @registry.add_binding(Keys.ControlJ, filter=in_prompt_mode("help") & is_returnable)
    def _(event):
        buff = event.current_buffer
        buff.accept_action.validate_and_handle(event.cli, buff)

    @registry.add_binding(Keys.ControlC, filter=in_prompt_mode("help"))
    def _(event):
        multi_prompt.mode = "r"

    # debug prompt

    @registry.add_binding(Keys.ControlP, filter=in_prompt_mode("debug"))
    def _(event):
        multi_prompt.mode = "r"

    @registry.add_binding(Keys.ControlJ, filter=in_prompt_mode("debug") & is_returnable)
    def _(event):
        buff = event.current_buffer
        buff.accept_action.validate_and_handle(event.cli, buff)

    return registry


def create_accept_action(multi_prompt):

    _globals = {"api": api, "interface": interface}
    _locals = {}

    def _process_input(cli, buffer):
        text = buffer.text
        if len(text.strip()) > 0:
            if multi_prompt.mode == "r":
                try:
                    Rinstance.is_busy = True
                    result = interface.reval(text)
                    if api.visible():
                        # todo: use cli.output.write
                        interface.rprint(result)
                except SyntaxError as e:
                    cli.output.write(str(e))
                    cli.output.write("\n")
                except RuntimeError as e:
                    pass
                finally:
                    Rinstance.is_busy = False

            elif multi_prompt.mode == "debug":
                try:
                    try:
                        result = eval(text, _globals, _locals)
                        if result:
                            # todo: use cli.output.write
                            print(result)

                    except SyntaxError:
                        exec(text, _globals, _locals)

                except Exception:
                    traceback.print_exc()

            buffer.reset(append_to_history=True)

        # print a new line between prompts
        cli.output.write("\n")

    return AcceptAction.run_in_terminal(_process_input, render_cli_done=True)


def create_r_repl_application():

    multi_prompt = MultiPrompt()

    registry = create_key_registry(multi_prompt)

    def get_prompt_tokens(cli):
        return [(Token.Prompt, multi_prompt.prompt)]

    accept_action = create_accept_action(multi_prompt)

    history = FileHistory(os.path.join(os.path.expanduser("~"), ".ride_history"))

    application = create_prompt_application(
        get_prompt_tokens=get_prompt_tokens,
        key_bindings_registry=registry,
        multiline=True,
        history=history,
        completer=RCompleter(multi_prompt),
        complete_while_typing=True,
        accept_action=accept_action,
        on_exit=AbortAction.RETURN_NONE)

    application.on_start = lambda cli: cli.output.write(interface.r_version() + "\n")

    return application


def create_r_eventloop():
    def process_events(context):
        while True:
            if context.input_is_ready() or Rinstance.is_busy:
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


def create_r_command_line_interface():
    application = create_r_repl_application()
    eventloop = create_r_eventloop()
    return RCommandlineInterface(
            application=application,
            eventloop=eventloop)
