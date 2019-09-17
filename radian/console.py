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
            session.app.output.write("\n")

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
                    sys.exit(1)

            current_mode = session.current_mode

            if not current_mode.native:
                result = current_mode.on_done(session)
                if result is not None:
                    return result
                if settings.insert_new_line and current_mode.insert_new_line:
                    session.app.output.write("\n")
                text = None

        return text

    return read_console


def create_write_console_ex(session, stderr_format):
    from prompt_toolkit.formatted_text import ANSI
    from prompt_toolkit.shortcuts import print_formatted_text

    # color_depth = session.color_depth

    def write_console_ex(buf, otype):
        if otype == 0:
            if sys.stdout:
                sys.stdout.write(buf)
                sys.stdout.flush()
                TERMINAL_CURSOR_AT_BEGINNING[0] = buf.replace("\r", "\n").endswith("\n")
        else:
            if sys.stderr:
                print_formatted_text(ANSI(stderr_format.format(buf)), end="", file=sys.stderr)
                sys.stderr.flush()
                TERMINAL_CURSOR_AT_BEGINNING[0] = buf.replace("\r", "\n").endswith("\n")

    return write_console_ex
