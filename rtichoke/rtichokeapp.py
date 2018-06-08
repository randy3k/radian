from __future__ import unicode_literals
import sys
import os

from . import callbacks

import rapi
from rapi import rcopy, rsym, rcall, namespace
from rapi import Machine
import struct

from .prompt import create_rtichoke_prompt_session, intialize_modes, session_initialize


def interrupts_pending(pending=True):
    if sys.platform == "win32":
        rapi.internals.UserBreak.value = int(pending)
    else:
        rapi.internals.R_interrupts_pending.value = int(pending)


def check_user_interrupt():
    rapi.internals.R_CheckUserInterrupt()


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
                    print("please report to https://github.com/randy3k/rtichoke for such error.")
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


class RtichokeApplication(object):
    instance = None
    r_home = None

    def __init__(self, r_home, ver):
        RtichokeApplication.instance = self
        self.r_home = r_home
        self.ver = ver
        super(RtichokeApplication, self).__init__()

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
            if not os.path.exists(".rtichoke_history"):
                open(".rtichoke_history", 'w+').close()

        os.environ["RETICULATE_PYTHON"] = sys.executable

        os.environ["R_DOC_DIR"] = os.path.join(self.r_home, "doc")
        os.environ["R_INCLUDE_DIR"] = os.path.join(self.r_home, "include")
        os.environ["R_SHARE_DIR"] = os.path.join(self.r_home, "share")

    def run(self, options):
        self.set_env_vars(options)

        args = ["rapi", "--quiet", "--no-restore-history"]

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

        if options.restore_data:
            args.append("--restore-data")
        else:
            args.append("--no-restore-data")

        session = create_rtichoke_prompt_session(options, history_file=".rtichoke_history")
        self.session = session

        m = Machine(set_default_callbacks=False, verbose=options.debug)
        m.set_callback("R_ShowMessage", callbacks.show_message)
        m.set_callback("R_ReadConsole", callbacks.create_read_console(get_prompt(session)))
        m.set_callback("R_WriteConsoleEx", callbacks.write_console_ex)
        m.set_callback("R_Busy", callbacks.busy)
        m.set_callback("R_PolledEvents", callbacks.polled_events)
        m.set_callback("R_YesNoCancel", callbacks.ask_yes_no_cancel)
        m.start(arguments=args)
        self.machine = m

        session_initialize(session)
        intialize_modes(session)

        ns = namespace.make_namespace("rtichoke", version=self.ver)
        namespace.assign("version", self.ver, ns)
        namespace.namespace_export(ns, [
            "version"
        ])
        namespace.seal_namespace(ns)

        # print welcome message
        session.app.output.write(greeting())

        m.run_loop()


def main():
    import optparse
    import os
    import sys
    from rapi.utils import which_rhome, rversion2
    from rtichoke import __version__

    parser = optparse.OptionParser("usage: rtichoke")
    parser.add_option("-v", "--version", action="store_true", dest="version", help="get version")
    parser.add_option("--no-environ", action="store_true", dest="no_environ", help="Don't read the site and user environment files")
    parser.add_option("--no-site-file", action="store_true", dest="no_site_file", help="Don't read the site-wide Rprofile")
    parser.add_option("--no-init-file", action="store_true", dest="no_init_file", help="Don't read the user R profile")
    parser.add_option("--local-history", action="store_true", dest="local_history", help="Force using local history file")
    parser.add_option("--global-history", action="store_true", dest="global_history", help="Force using global history file")
    parser.add_option("--no-history", action="store_true", dest="no_history", help="Don't load any history files")
    parser.add_option("--vanilla", action="store_true", dest="vanilla", help="Combine --no-history --no-environ --no-site-file --no-init-file")
    parser.add_option("--ask-save", action="store_true", dest="ask_save", help="Ask to save R data")
    parser.add_option("--restore-data", action="store_true", dest="restore_data", help="Restore previously saved objects")
    parser.add_option("--debug", action="store_true", dest="debug", help="Debug mode")

    options, args = parser.parse_args()

    r_home = which_rhome()

    if options.version:
        if r_home:
            r_binary = os.path.normpath(os.path.join(r_home, "bin", "R"))
            r_version = rversion2(r_home)
        else:
            r_binary = "NA"
            r_version = "NA"
        print("rtichoke version: {}".format(__version__))
        print("r executable: {}".format(r_binary))
        print("r version: {}".format(r_version))
        print("python executable: {}".format(sys.executable))
        print("python version: {:d}.{:d}.{:d}".format(
            sys.version_info.major,
            sys.version_info.minor,
            sys.version_info.micro))
        return

    os.environ["RTICHOKE_VERSION"] = __version__
    os.environ["RTICHOKE_COMMAND_ARGS"] = " ".join(
        ["--" + k.replace("_", "-") for k, v in options.__dict__.items() if v])

    if not r_home:
        raise RuntimeError("Cannot find R binary. Expose it via the `PATH` variable.")

    RtichokeApplication(r_home, ver=__version__).run(options)


def get_app():
    return RtichokeApplication.instance
