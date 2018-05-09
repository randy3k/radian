from __future__ import unicode_literals
import sys
import time
import os
import re

from . import callbacks

import rapi
from rapi import get_libR, embedded, ensure_path, bootstrap, interface
from rapi import rcopy, rsym, rcall
from rapi.utils import cglobal, ccall

from ctypes import c_int
import struct

from prompt_toolkit.application.current import get_app
from prompt_toolkit.eventloop import set_event_loop

from prompt_toolkit.styles import style_from_pygments_cls
from pygments.styles import get_style_by_name

from prompt_toolkit.formatted_text import ANSI
from prompt_toolkit.enums import EditingMode

from .rtichokeprompt import create_rtichoke_prompt


PROMPT = "\x1b[34mr$>\x1b[0m "
SHELL_PROMPT = "\x1b[31m#!>\x1b[0m "
BROWSE_PROMPT = "\x1b[33mBrowse[{}]>\x1b[0m "
BROWSE_PATTERN = re.compile(r"Browse\[([0-9]+)\]> $")


RETICULATE_MESSAGE = """
The host python environment is {}
and `rtichoke` is forcing `reticulate` to use this version of python.
Any python packages needed, e.g., `tensorflow` and `keras`,
have to be available to the current python environment.

File an issue at https://github.com/randy3k/rtichoke if you encounter any
difficulties in loading `reticulate`.
""".format(sys.executable).strip()


def interrupts_pending(pending=True):
    if sys.platform == "win32":
        cglobal("UserBreak", rapi.libR, c_int).value = int(pending)
    else:
        cglobal("R_interrupts_pending", rapi.libR, c_int).value = int(pending)


def check_user_interrupt():
    ccall("R_CheckUserInterrupt", rapi.libR, None, [])


def reticulate_set_message(message):
    rapi.reval("""
    setHook(packageEvent("reticulate", "onLoad"),
            function(...) packageStartupMessage("{}"))
    """.format(message.replace('\\', '\\\\').replace('"', '\\"')))


def greeting():
    info = rcopy(rcall(rsym("R.Version")))
    return "{} -- \"{}\"\nPlatform: {} ({}-bit)\n".format(
        info["version.string"], info["nickname"], info["platform"], 8 * struct.calcsize("P"))


class RtichokeApplication(object):
    initialized = False
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

    def app_initialize(self, mp):
        if not interface.get_option("rtichoke.suppress_reticulate_message", False):
            reticulate_set_message(RETICULATE_MESSAGE)

        if interface.get_option("rtichoke.editing_mode", "emacs") in ["vim", "vi"]:
            mp.app.editing_mode = EditingMode.VI
        else:
            mp.app.editing_mode = EditingMode.EMACS

        color_scheme = interface.get_option("rtichoke.color_scheme", "native")
        mp.style = style_from_pygments_cls(get_style_by_name(color_scheme))

        mp.app.auto_match = interface.get_option("rtichoke.auto_match", False)
        mp.app.auto_indentation = interface.get_option("rtichoke.auto_indentation", True)
        mp.app.tab_size = int(interface.get_option("rtichoke.tab_size", 4))
        mp.complete_while_typing = interface.get_option("rtichoke.complete_while_typing", True)
        mp.history_search_no_duplicates = interface.get_option("rtichoke.history_search_no_duplicates", False)
        mp.insert_new_line = interface.get_option("rtichoke.insert_new_line", True)

        prompt = interface.get_option("rtichoke.prompt", None)
        if prompt:
            mp.set_prompt_mode_message("r", ANSI(prompt))
        else:
            sys_prompt = interface.get_option("prompt")
            if sys_prompt == "> ":
                prompt = PROMPT
            else:
                prompt = sys_prompt

        mp.default_prompt = prompt
        mp.set_prompt_mode_message("r", ANSI(prompt))
        interface.set_option("prompt", prompt)

        shell_prompt = interface.get_option("rtichoke.shell_prompt", SHELL_PROMPT)
        mp.set_prompt_mode_message("shell", ANSI(shell_prompt))

        mp.browse_prompt = interface.get_option("rtichoke.browse_prompt", BROWSE_PROMPT)

        set_width_on_resize = interface.get_option("setWidthOnResize", True)
        mp.auto_width = interface.get_option("rtichoke.auto_width", set_width_on_resize)
        output_width = mp.app.output.get_size().columns
        if output_width and mp.auto_width:
            interface.set_option("width", output_width)
        mp.completion_timeout = interface.get_option("rtichoke.completion_timeout", 0.05)

        # necessary on windows
        interface.set_option("menu.graphics", False)

        # enables completion of installed package names
        if interface.rcopy(interface.reval("rc.settings('ipck')")) is None:
            interface.reval("rc.settings(ipck = TRUE)")

        # print welcome message
        mp.app.output.write(greeting())

    def get_inputhook(self):
        terminal_width = [None]

        def process_events(context):
            tic = 0
            while True:
                if context.input_is_ready():
                    break
                interface.process_events()

                app = get_app()
                if tic == 10:
                    tic = 0
                    output_width = app.output.get_size().columns
                    if output_width and terminal_width[0] != output_width:
                        terminal_width[0] = output_width
                        interface.set_option("width", max(terminal_width[0], 20))

                tic += 1

                time.sleep(1.0 / 30)

        return process_events

    def run(self, options):
        self.set_env_vars(options)

        mp = create_rtichoke_prompt(
            options, history_file=".rtichoke_history", inputhook=self.get_inputhook())
        interrupted = [False]

        def result_from_prompt(message, add_history=1):
            if not self.initialized:
                self.app_initialize(mp)
                message = mp.default_prompt
                self.initialized = True
                mp.app.output.write("\n")
            else:
                if interrupted[0]:
                    interrupted[0] = False
                elif mp.insert_new_line:
                    mp.app.output.write("\n")

            mp.add_history = add_history == 1

            text = None

            # a hack to stop rtichoke when exiting if an error occurs in process_events
            # however, please note that it doesn't in general guarantee to work
            # the best practice is to restart rtichoke
            if mp.app._is_running:
                mp.app._is_running = False
                set_event_loop(None)

            while text is None:
                try:
                    if message == mp.default_prompt:
                        mp.prompt_mode = "r"
                    elif BROWSE_PATTERN.match(message):
                        level = BROWSE_PATTERN.match(message).group(1)
                        mp.prompt_mode = "browse"
                        mp.set_prompt_mode_message(
                            "browse",
                            ANSI(mp.browse_prompt.format(level)))
                    else:
                        # invoked by `readline`
                        mp.prompt_mode = "readline"
                        mp.set_prompt_mode_message("readline", ANSI(message))

                    text = mp.run()

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
                    if mp.prompt_mode in ["readline"]:
                        interrupted[0] = True
                        interrupts_pending(True)
                        check_user_interrupt()
                    elif mp.insert_new_line:
                        mp.app.output.write("\n")

            return text

        ensure_path(self.r_home)
        libR = get_libR(self.r_home)

        embedded.set_callback("R_ShowMessage", callbacks.show_message)
        embedded.set_callback("R_ReadConsole", callbacks.create_read_console(result_from_prompt))
        embedded.set_callback("R_WriteConsoleEx", callbacks.write_console_ex)
        embedded.set_callback("R_Busy", rapi.defaults.R_Busy)
        embedded.set_callback("R_PolledEvents", rapi.defaults.R_PolledEvents)
        embedded.set_callback("R_YesNoCancel", rapi.defaults.R_YesNoCancel)

        embedded.initialize(libR, arguments=["rapi", "--quiet", "--no-save"])

        bootstrap(libR, verbose=True)  # should be set False
        embedded.run_loop(libR)
