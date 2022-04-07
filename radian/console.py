import signal
import re
from contextlib import contextmanager

from .settings import radian_settings as settings
from rchitect import console


TERMINAL_CURSOR_AT_BEGINNING = [True]

SUPPRESS_STDOUT = False
SUPPRESS_STDERR = False
ANSI_ESCAPE_RE = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')


def normalize(string):
    return ANSI_ESCAPE_RE.sub('', string.replace('\r\n', '\n').replace('\r', '\n'))


@contextmanager
def suppress_stderr(suppress=True):
    """
    It is used in completion to avoid running prompt-toolkit nestedly
    """
    global SUPPRESS_STDERR
    OLD_SUPPRESS_STDERR = SUPPRESS_STDERR
    SUPPRESS_STDERR = suppress
    try:
        yield
    finally:
        console.flush()
        SUPPRESS_STDERR = OLD_SUPPRESS_STDERR


def sigint_handler(signum, frame):
    raise KeyboardInterrupt()


def ask_input(s):
    orig_handler = signal.getsignal(signal.SIGINT)
    # allow Ctrl+C to throw KeyboardInterrupt in callback
    signal.signal(signal.SIGINT, sigint_handler)
    try:
        return input(s)
    finally:
        signal.signal(signal.SIGINT, orig_handler)


def native_prompt(app, message):
    # c.f. run_coroutine_in_terminal of prompt_toolkit
    with suppress_stderr(False):
        console.flush()
        app.output.flush()
        app._running_in_terminal = True
        try:
            with app.input.detach():
                with app.input.cooked_mode():
                    return ask_input(message)
        except KeyboardInterrupt:
            app.output.write_raw("\n")
            raise
        finally:
            app._running_in_terminal = False
            app.renderer.reset()
            app._request_absolute_cursor_position()
            app._redraw()


def create_read_console(session):
    interrupted = [False]

    def _read_console(message, add_history=1):
        app = session.app

        if app.is_running:
            # fallback to `input` if `read_console` is called nestedly
            return native_prompt(app, message)

        session._prompt_message = message
        current_mode_spec = session.current_mode_spec

        if interrupted[0]:
            interrupted[0] = False
            if not session.current_mode_spec.sticky_on_sigint:
                session.activate_mode(session.mode_to_be_activated())
            if current_mode_spec.insert_new_line_on_sigint:
                app.output.write_raw("\n")
        elif not TERMINAL_CURSOR_AT_BEGINNING[0] or \
                (settings.insert_new_line and current_mode_spec.insert_new_line):
            app.output.write_raw("\n")

        text = None

        while text is None:
            if not session.current_mode_spec.sticky:
                session.activate_mode(session.mode_to_be_activated())

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

            if text is None and settings.insert_new_line and current_mode_spec.insert_new_line:
                app.output.write_raw("\n")

        return text

    def read_console(message, add_history):
        return _read_console(message, add_history)

    return read_console


def create_write_console_ex(session, stderr_format):
    app = session.app
    output = app.output
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
                    if not SUPPRESS_STDOUT:
                        buf = buf.replace("\r\n", "\n")
                        sbuf = buf.split("\r")
                        for i, b in enumerate(sbuf):
                            print_formatted_text(ANSI(b), end="", output=output)
                            if i < len(sbuf) - 1:
                                output.write("\r")
                        output.flush()
                        TERMINAL_CURSOR_AT_BEGINNING[0] = buf.endswith("\n")
                else:
                    if not SUPPRESS_STDERR:
                        buf = buf.replace("\r\n", "\n")
                        sbuf = buf.split("\r")
                        for i, b in enumerate(sbuf):
                            print_formatted_text(
                                ANSI(stderr_format.format(b)), end="", output=output)
                            if i < len(sbuf) - 1:
                                output.write("\r")
                        output.flush()
                        TERMINAL_CURSOR_AT_BEGINNING[0] = normalize(buf).endswith("\n")

    if not write_console_ex:
        def write_console_ex(buf, otype):
            if otype == 0:
                if not SUPPRESS_STDOUT:
                    output.write_raw(buf)
                    output.flush()
                    TERMINAL_CURSOR_AT_BEGINNING[0] = normalize(buf).endswith("\n")
            else:
                if not SUPPRESS_STDERR:
                    output.write_raw(stderr_format.format(buf))
                    output.flush()
                    TERMINAL_CURSOR_AT_BEGINNING[0] = normalize(buf).endswith("\n")

    return write_console_ex
