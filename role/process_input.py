import traceback

from . import api
from . import interface


def prase_input_complete(cli):
    return api.parse_vector(api.mk_string(cli.current_buffer.text))[1] != 2


def _process_input(cli, status):
    code = cli.current_buffer.text
    try:
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

    cli.output.write("\n")


def process_input(cli):
    text = cli.current_buffer.text
    lines = text.strip("\n").split("\n")
    lineno = 0
    status = [True]
    for i in range(len(lines)):
        code = "\n".join(lines[lineno:(i+1)]).strip("\n")
        if len(code) > 0:
            if api.parse_vector(api.mk_string(code))[1] != 2:
                lineno = i + 1
                cli.current_buffer.cursor_position = 0
                cli.current_buffer.text = code
                cli.run_in_terminal(lambda: _process_input(cli, status), render_cli_done=True)
                if not status[0]:
                    break


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
