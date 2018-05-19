from __future__ import unicode_literals
import sys
import os
import re

from . import callbacks

import rapi
from rapi import rcopy, rsym, rcall
import struct

from .prompt import create_rtichoke_prompt_session, intialize_modes, session_initialize
from .shell import run_command

BROWSE_PATTERN = re.compile(r"Browse\[([0-9]+)\]> $")


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
        if message == session.default_prompt:
            session.activate_mode("r")
        elif BROWSE_PATTERN.match(message):
            session.browse_level = BROWSE_PATTERN.match(message).group(1)
            session.activate_mode("browse")
        else:
            # invoked by `readline`
            session.activate_mode("readline")
            session.readline_prompt = message

        if interrupted[0]:
            interrupted[0] = False
        elif session.insert_new_line and session.current_mode_name is not "readline":
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
                if session.current_mode_name in ["readline"]:
                    interrupted[0] = True
                    interrupts_pending(True)
                    check_user_interrupt()
                elif session.insert_new_line:
                    session.app.output.write("\n")

            if session.current_mode_name == "shell":
                session.default_buffer.reset()
                run_command(text)
                text = None

        return text

    return _


class RtichokeApplication(object):
    r_home = None

    def __init__(self, r_home):
        self.r_home = r_home
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

        session = create_rtichoke_prompt_session(options, history_file=".rtichoke_history")

        rapi.utils.ensure_path(self.r_home)
        libR = rapi.utils.find_libR(self.r_home)

        rapi.embedded.set_callback("R_ShowMessage", callbacks.show_message)
        rapi.embedded.set_callback("R_ReadConsole", callbacks.create_read_console(get_prompt(session)))
        rapi.embedded.set_callback("R_WriteConsoleEx", callbacks.write_console_ex)
        rapi.embedded.set_callback("R_Busy", callbacks.busy)
        rapi.embedded.set_callback("R_PolledEvents", callbacks.polled_events)
        rapi.embedded.set_callback("R_YesNoCancel", callbacks.ask_yes_no_cancel)

        args = ["rapi", "--quiet", "--no-restore-history"]

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

        rapi.embedded.initialize(libR, arguments=args)

        rapi.bootstrap(libR, verbose=options.debug)

        session_initialize(session)

        intialize_modes(session)

        # print welcome message
        session.app.output.write(greeting())

        rapi.embedded.run_loop(libR)
