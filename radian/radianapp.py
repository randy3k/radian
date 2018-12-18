from __future__ import unicode_literals
import os
import sys
import struct

from rchitect import rcopy, rsym, rcall, namespace
from rchitect import internals, Machine


def interrupts_pending(pending=True):
    if sys.platform == "win32":
        internals.UserBreak.value = int(pending)
    else:
        internals.R_interrupts_pending.value = int(pending)


def check_user_interrupt():
    internals.R_CheckUserInterrupt()


def greeting():
    info = rcopy(rcall(rsym("R.Version")))
    return "{} -- \"{}\"\nPlatform: {} ({}-bit)\n".format(
        info["version.string"], info["nickname"], info["platform"], 8 * struct.calcsize("P"))


def get_prompt(session):
    interrupted = [False]

    def _(message, add_history=1):
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
            except KeyboardInterrupt:
                interrupted[0] = True

            current_mode = session.current_mode

            if interrupted[0]:
                if current_mode.native:
                    interrupts_pending(True)
                    check_user_interrupt()
                elif session.insert_new_line and session.current_mode.insert_new_line:
                    session.app.output.write("\n")
                    interrupted[0] = False
                    text = None
            elif not current_mode.native:
                result = current_mode.on_done(session)
                if current_mode.return_result and current_mode.return_result(result):
                    return result
                if session.insert_new_line and current_mode.insert_new_line:
                    session.app.output.write("\n")
                text = None

        return text

    return _


class RadianApplication(object):
    instance = None
    r_home = None

    def __init__(self, r_home, ver):
        RadianApplication.instance = self
        self.r_home = r_home
        self.ver = ver
        super(RadianApplication, self).__init__()

    def set_env_vars(self, options):
        if options.vanilla:
            options.no_history = True
            options.no_environ = True
            options.no_site_file = True
            options.no_init_file = True

        if options.no_environ:
            os.environ["R_ENVIRON"] = ""
            os.environ["R_ENVIRON_USER"] = ""

        if options.no_site_file:
            os.environ["R_PROFILE"] = ""

        if options.no_init_file:
            os.environ["R_PROFILE_USER"] = ""

        if options.local_history:
            if not os.path.exists(".radian_history"):
                open(".radian_history", 'w+').close()

        os.environ["RETICULATE_PYTHON"] = sys.executable

        os.environ["R_DOC_DIR"] = os.path.join(self.r_home, "doc")
        os.environ["R_INCLUDE_DIR"] = os.path.join(self.r_home, "include")
        os.environ["R_SHARE_DIR"] = os.path.join(self.r_home, "share")

    def run(self, options):
        from .prompt import create_radian_prompt_session, intialize_modes, session_initialize
        from . import callbacks

        self.set_env_vars(options)

        args = ["rchitect", "--quiet", "--no-restore-history"]

        if sys.platform != "win32":
            args.append("--no-readline")

        if options.no_environ:
            args.append("--no-environ")

        if options.no_site_file:
            args.append("--no-site-file")

        if options.no_init_file:
            args.append("--no-init-file")

        if options.ask_save is not True:
            args.append("--no-save")

        if options.restore_data is not True:
            args.append("--no-restore-data")

        self.session = create_radian_prompt_session(options, history_file=".radian_history")
        session = self.session

        self.m = Machine(set_default_callbacks=False, verbose=options.debug)
        m = self.m
        m.set_callback("R_ShowMessage", callbacks.show_message)
        m.set_callback("R_ReadConsole", callbacks.create_read_console(get_prompt(session)))
        m.set_callback("R_WriteConsoleEx", callbacks.write_console_ex)
        m.set_callback("R_Busy", callbacks.busy)
        m.set_callback("R_PolledEvents", callbacks.polled_events)
        m.set_callback("R_YesNoCancel", callbacks.ask_yes_no_cancel)
        m.start(arguments=args)

        session_initialize(session)
        intialize_modes(session)

        # namespace.register_py_namespace()
        # ns = namespace.make_namespace("radian", version=self.ver)
        # namespace.assign("version", self.ver, ns)
        # namespace.namespace_export(ns, [
        #     "version"
        # ])
        # namespace.seal_namespace(ns)

        # print welcome message
        if options.quiet is not True:
            session.app.output.write(greeting())

        m.run_loop()
