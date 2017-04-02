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
from prompt_toolkit.enums import DEFAULT_BUFFER
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


def _process_input(cli, status):
    code = cli.current_buffer.text
    try:
        Rinstance.is_busy = True
        result = interface.reval(code)
        if api.visible():
            # todo: use cli.output.write
            interface.rprint(result)
    except SyntaxError as e:
        status[0] = False
        print(e)
    except RuntimeError as e:
        status[0] = False
        pass
    finally:
        cli.current_buffer.reset(append_to_history=True)
        Rinstance.is_busy = False

    cli.output.write("\n")


def process_input(cli):
    text = cli.current_buffer.text
    lines = text.strip("\n").split("\n")
    lineno = 0
    status = [True]
    for i in range(len(lines)):
        code = "\n".join(lines[lineno:(i+1)]).strip("\n")
        if len(code) > 0:
            if api.parse_vector(api.mk_string(code))[1] == 1:
                lineno = i + 1
                cli.current_buffer.cursor_position = 0
                cli.current_buffer.text = code
                cli.run_in_terminal(lambda: _process_input(cli, status), render_cli_done=True)
                if not status[0]:
                    break

    cli.current_buffer.insert_text("\n".join(lines[lineno:]).strip("\n"))


_globals = {"api": api, "interface": interface}
_locals = {}


def process_python_input(cli):
    text = cli.current_buffer.text
    if len(text.strip()) > 0:
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

        cli.current_buffer.reset(append_to_history=True)

    # print a new line between prompts
    cli.output.write("\n")


def create_key_registry(multi_prompt):
    registry = load_key_bindings_for_prompt(enable_system_bindings=True)

    is_begining_of_line = Condition(lambda cli: cli.current_buffer.cursor_position == 0)
    is_default_buffer = Condition(lambda cli: cli.current_buffer_name == DEFAULT_BUFFER)

    @Condition
    def prase_complete(cli):
        return api.parse_vector(api.mk_string(cli.current_buffer.text))[1] != 2

    def in_prompt_mode(m):
        return Condition(lambda _: multi_prompt.mode == m)

    # R prompt

    @registry.add_binding(Keys.ControlJ, filter=is_default_buffer & in_prompt_mode("r") & prase_complete)
    def _(event):
        process_input(event.cli)

    @registry.add_binding("?", filter=is_default_buffer & in_prompt_mode("r") & is_begining_of_line)
    def _(event):
        multi_prompt.mode = "help"

    @registry.add_binding(Keys.ControlP, filter=is_default_buffer & in_prompt_mode("r"))
    def _(event):
        multi_prompt.mode = "debug"

    @registry.add_binding(Keys.BracketedPaste, filter=is_default_buffer & in_prompt_mode("r"))
    def _(event):
        data = event.data
        data = data.replace('\r\n', '\n')
        data = data.replace('\r', '\n')
        event.current_buffer.insert_text(data)
        if data[-1] == "\n":
            process_input(event.cli)

    # help prompt

    @registry.add_binding(Keys.Backspace, filter=is_default_buffer & in_prompt_mode("help") & is_begining_of_line)
    def _(event):
        multi_prompt.mode = "r"

    @registry.add_binding(Keys.ControlJ, filter=is_default_buffer & in_prompt_mode("help"))
    def _(event):
        pass

    @registry.add_binding(Keys.ControlC, filter=is_default_buffer & in_prompt_mode("help"))
    def _(event):
        multi_prompt.mode = "r"

    # debug prompt

    @registry.add_binding(Keys.ControlP, filter=is_default_buffer & in_prompt_mode("debug"))
    def _(event):
        multi_prompt.mode = "r"

    @registry.add_binding(Keys.ControlJ, filter=is_default_buffer & in_prompt_mode("debug"))
    def _(event):
        event.cli.run_in_terminal(lambda: process_python_input(event.cli), render_cli_done=True)

    return registry


def create_r_repl_application():

    multi_prompt = MultiPrompt()

    registry = create_key_registry(multi_prompt)

    def get_prompt_tokens(cli):
        return [(Token.Prompt, multi_prompt.prompt)]

    history = FileHistory(os.path.join(os.path.expanduser("~"), ".ride_history"))

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
