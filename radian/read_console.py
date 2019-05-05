from __future__ import unicode_literals
import sys


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
        elif session.insert_new_line and current_mode.insert_new_line:
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
                if session.insert_new_line and current_mode.insert_new_line:
                    session.app.output.write("\n")
                text = None

        return text

    return read_console
