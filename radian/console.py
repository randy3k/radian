from __future__ import unicode_literals
import sys

from radian.settings import radian_settings as settings
from rchitect import console
from contextlib import contextmanager


TERMINAL_CURSOR_AT_BEGINNING = [True]

CALLING_FROM_PROMPT = False
SUPPRESS_STDOUT = False
SUPPRESS_STDERR = False


if sys.version >= "3":
    def ask_input(s):
        return input(s)
else:
    def ask_input(s):
        return raw_input(s).decode("utf-8", "backslashreplace")


@contextmanager
def native_read_console():
    """
    It is used in completion to avoid running prompt-toolkit nestedly
    """
    global CALLING_FROM_PROMPT
    global SUPPRESS_STDERR
    CALLING_FROM_PROMPT = True
    SUPPRESS_STDERR = True
    try:
        yield
    finally:
        CALLING_FROM_PROMPT = False
        SUPPRESS_STDERR = False


def create_read_console(session):
    interrupted = [False]

    def read_console(message, add_history=1):

        if CALLING_FROM_PROMPT:
            # fallback to `input` if `read_console` is called nestedly
            # c.f. run_coroutine_in_terminal of prompt_toolkit
            global SUPPRESS_STDERR
            OLD_SUPPRESS_STDERR = SUPPRESS_STDERR
            SUPPRESS_STDERR = False
            app = session.app
            console.flush()
            app.output.flush()
            app._running_in_terminal = True
            try:
                with app.input.detach():
                    with app.input.cooked_mode():
                        return ask_input(message)
            finally:
                SUPPRESS_STDERR = OLD_SUPPRESS_STDERR
                app._running_in_terminal = False
                app.renderer.reset()
                app._request_absolute_cursor_position()
                app._redraw()

        session.prompt_text = message

        activated = False
        for name in reversed(session.modes):
            mode = session.modes[name]
            if mode.activator and mode.activator(session):
                session.activate_mode(name)
                activated = True
                break
        if not activated:
            session.activate_mode("unknown")

        current_mode = session.current_mode

        if interrupted[0]:
            interrupted[0] = False
        elif not TERMINAL_CURSOR_AT_BEGINNING[0] or \
                (settings.insert_new_line and current_mode.insert_new_line):
            session.app.output.write_raw("\n")

        text = None

        while text is None:
            try:
                text = session.prompt(add_history=add_history)

            except KeyboardInterrupt:
                interrupted[0] = True
                raise

            except Exception as e:
                if isinstance(e, EOFError):
                    # todo: confirmation in "r" mode
                    return None
                else:
                    print("unexpected error was caught.")
                    print("please report to https://github.com/randy3k/radian for such error.")
                    print(e)
                    import traceback
                    traceback.print_exc()
                    import os
                    os._exit(1)

            current_mode = session.current_mode

            if current_mode.on_post_accept:
                result = current_mode.on_post_accept(session)
                if result is not None:
                    return result
                if settings.insert_new_line and current_mode.insert_new_line:
                    session.app.output.write_raw("\n")
                text = None

        return text

    return read_console


def create_write_console_ex(session, stderr_format):
    output = session.app.output
    from prompt_toolkit.utils import is_windows

    write_console_ex = None

    if is_windows():
        from prompt_toolkit.output.win32 import Win32Output
        if isinstance(output, Win32Output):
            # we use print_formatted_text to support ANSI sequences in older Windows
            from prompt_toolkit.formatted_text import ANSI
            from prompt_toolkit.shortcuts import print_formatted_text

            def write_console_ex(buf, otype):
                if otype == 0:
                    if sys.stdout:
                        buf = buf.replace("\r\n", "\n")
                        sbuf = buf.split("\r")
                        for i, b in enumerate(sbuf):
                            print_formatted_text(ANSI(b), end="", output=output)
                            if i < len(sbuf) - 1:
                                output.write("\r")
                        output.flush()
                        TERMINAL_CURSOR_AT_BEGINNING[0] = buf.endswith("\n")
                else:
                    if sys.stderr:
                        buf = buf.replace("\r\n", "\n")
                        sbuf = buf.split("\r")
                        for i, b in enumerate(sbuf):
                            print_formatted_text(
                                ANSI(stderr_format.format(b)), end="", output=output)
                            if i < len(sbuf) - 1:
                                output.write("\r")
                        output.flush()
                        TERMINAL_CURSOR_AT_BEGINNING[0] = buf.endswith("\n")

    if not write_console_ex:
        def write_console_ex(buf, otype):
            if otype == 0:
                if not SUPPRESS_STDOUT:
                    output.write_raw(buf)
                    output.flush()
                    TERMINAL_CURSOR_AT_BEGINNING[0] = buf.endswith("\n")
            else:
                if not SUPPRESS_STDERR:
                    output.write_raw(stderr_format.format(buf))
                    output.flush()
                    TERMINAL_CURSOR_AT_BEGINNING[0] = buf.endswith("\n")

    return write_console_ex
