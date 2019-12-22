from __future__ import unicode_literals
import sys

from radian.settings import radian_settings as settings


TERMINAL_CURSOR_AT_BEGINNING = [True]


def create_read_console(session):
    interrupted = [False]

    def read_console(message, add_history=1):
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
                # although we do not use sys.stdout and sys.stderr directly, we use them to flag
                # whether we should print to them
                if sys.stdout:
                    output.write_raw(buf)
                    output.flush()
                    TERMINAL_CURSOR_AT_BEGINNING[0] = buf.endswith("\n")
            else:
                if sys.stderr:
                    output.write_raw(stderr_format.format(buf))
                    output.flush()
                    TERMINAL_CURSOR_AT_BEGINNING[0] = buf.endswith("\n")

    return write_console_ex
