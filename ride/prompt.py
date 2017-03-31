from prompt_toolkit.shortcuts import \
    create_prompt_application, create_eventloop, CommandLineInterface, create_output
from prompt_toolkit.token import Token
from prompt_toolkit.key_binding.defaults import load_key_bindings_for_prompt
from prompt_toolkit.keys import Keys
from prompt_toolkit.filters import Condition, HasFocus
from prompt_toolkit.buffer import AcceptAction
from prompt_toolkit.interface import AbortAction
from prompt_toolkit.history import FileHistory
import time
import traceback

from .runtime import Rinstance
from . import api
from . import interface


class MultiPrompt(object):
    prompts = {
        "r": "r$> ",
        "help": "help?> ",
        "python": "python%> "
    }
    _prompt_mode = "r"

    @property
    def prompt(self):
        return self.prompts[self._prompt_mode]

    @property
    def prompt_mode(self):
        return self._prompt_mode

    @prompt_mode.setter
    def prompt_mode(self, m):
        self._prompt_mode = m


def create_key_registry(multi_prompt):
    registry = load_key_bindings_for_prompt(enable_system_bindings=True)

    is_begining_of_line = Condition(lambda cli: cli.current_buffer.cursor_position == 0)
    prase_complete = Condition(
        lambda cli: api.parse_vector(api.mk_string(cli.current_buffer.text))[1] != 2)

    is_returnable = Condition(lambda cli: cli.current_buffer.accept_action.is_returnable)

    def in_prompt_mode(m):
        return Condition(lambda _: multi_prompt.prompt_mode == m)

    # R prompt

    @registry.add_binding(Keys.ControlJ, filter=prase_complete & in_prompt_mode("r") & is_returnable)
    def _(event):
        buff = event.current_buffer
        buff.accept_action.validate_and_handle(event.cli, buff)

    @registry.add_binding("?", filter=is_begining_of_line & in_prompt_mode("r"))
    def _(event):
        multi_prompt.prompt_mode = "help"

    @registry.add_binding(Keys.ControlT, filter=in_prompt_mode("r"))
    def _(event):
        multi_prompt.prompt_mode = "python"

    # help prompt

    @registry.add_binding(Keys.Backspace, filter=is_begining_of_line & in_prompt_mode("help"))
    def _(event):
        multi_prompt.prompt_mode = "r"

    @registry.add_binding(Keys.ControlJ, filter=in_prompt_mode("help") & is_returnable)
    def _(event):
        buff = event.current_buffer
        buff.accept_action.validate_and_handle(event.cli, buff)

    # python prompt

    @registry.add_binding(Keys.ControlT, filter=in_prompt_mode("python"))
    def _(event):
        multi_prompt.prompt_mode = "r"

    @registry.add_binding(Keys.ControlJ, filter=in_prompt_mode("python") & is_returnable)
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
            if multi_prompt.prompt_mode == "r":
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

            elif multi_prompt.prompt_mode == "python":
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

    history = FileHistory(".consoler_history")

    application = create_prompt_application(
        get_prompt_tokens=get_prompt_tokens,
        key_bindings_registry=registry,
        multiline=True,
        history=history,
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

    return create_eventloop(inputhook=process_events)


class RCommandlineInterface(CommandLineInterface):

    def abort(self):
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
