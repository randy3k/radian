from __future__ import unicode_literals
import sys
import time
import os
import re

from .session import RSession
from . import interface
from . import api
from . import callbacks

from prompt_toolkit.application.current import get_app

from prompt_toolkit.styles import style_from_pygments
from pygments.styles import get_style_by_name

from prompt_toolkit.formatted_text import ANSI
from prompt_toolkit.enums import EditingMode

from .modalprompt import create_modal_prompt


PROMPT = "\x1b[34mr$>\x1b[0m "
SHELL_PROMPT = "\x1b[31m#!>\x1b[0m "
BROWSE_PROMPT = "\x1b[33mBrowse[{}]>\x1b[0m "
BROWSE_PATTERN = re.compile(r"Browse\[([0-9]+)\]> $")


RETICULATE_MESSAGE = """
The host python environment is {}
and `rice` is forcing `reticulate` to use this version of python.
Any python packages needed, e.g., `tensorflow` and `keras`,
have to be available to the current python environment.

File an issue at https://github.com/randy3k/rice if you encounter any
difficulties in loading `reticulate`.
""".format(sys.executable).strip()


class RiceApplication(object):
    initialized = False

    def set_cli_options(self, options):
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
            if not os.path.exists(".rice_history"):
                open(".rice_history", 'w+').close()

    def app_initialize(self, mp):
        if sys.platform.startswith('win'):
            encoding = api.encoding()
            callbacks.ENCODING = encoding

        if not interface.get_option("rice.suppress_reticulate_message", False):
            interface.reticulate_set_message(RETICULATE_MESSAGE)

        if interface.get_option("rice.editing_mode", "emacs") in ["vim", "vi"]:
            mp.app.editing_mode = EditingMode.VI
        else:
            mp.app.editing_mode = EditingMode.EMACS

        color_scheme = interface.get_option("rice.color_scheme", "native")
        mp.style = style_from_pygments(get_style_by_name(color_scheme))

        mp.app.auto_match = interface.get_option("rice.auto_match", False)
        mp.app.auto_indentation = interface.get_option("rice.auto_indentation", True)
        mp.app.tab_size = int(interface.get_option("rice.tab_size", 4))
        mp.complete_while_typing = interface.get_option("rice.complete_while_typing", True)
        mp.history_search_no_duplicates = interface.get_option("rice.history_search_no_duplicates", False)
        mp.insert_new_line = interface.get_option("rice.insert_new_line", True)

        prompt = interface.get_option("rice.prompt", None)
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

        shell_prompt = interface.get_option("rice.shell_prompt", SHELL_PROMPT)
        mp.set_prompt_mode_message("shell", ANSI(shell_prompt))

        mp.browse_prompt = interface.get_option("rice.browse_prompt", BROWSE_PROMPT)

        set_width_on_resize = interface.get_option("setWidthOnResize", True)
        mp.auto_width = interface.get_option("rice.auto_width", set_width_on_resize)

        if mp.auto_width:
            interface.set_option("width", mp.app.output.get_size().columns)

        # necessary on windows
        interface.set_option("menu.graphics", False)

        # enables completion of installed package names
        if interface.rcopy(interface.reval("rc.settings('ipck')")) is None:
            interface.reval("rc.settings(ipck = TRUE)")

        interface.installed_packages()

        # print welcome message
        sys.stdout.write(interface.greeting())

    def get_inputhook(self):
        terminal_width = [None]

        def process_events(context):
            tic = 0
            while True:
                if context.input_is_ready():
                    break
                api.process_events()

                app = get_app()
                if tic == 10:
                    tic = 0
                    output_width = app.output.get_size().columns
                    if terminal_width[0] != output_width:
                        terminal_width[0] = output_width
                        interface.set_option("width", max(terminal_width[0], 20))

                tic += 1

                time.sleep(1.0 / 30)

        return process_events

    def run(self, options):
        self.set_cli_options(options)

        mp = create_modal_prompt(options, history_file=".rice_history", inputhook=self.get_inputhook())
        mp.interrupted = False

        def result_from_prompt(message, add_history=1):
            if not self.initialized:
                self.app_initialize(mp)
                message = mp.default_prompt
                self.initialized = True
                sys.stdout.write("\n")
            else:
                if mp.interrupted:
                    mp.interrupted = False
                if mp.insert_new_line:
                    sys.stdout.write("\n")

            mp.add_history = add_history == 1

            text = None
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
                        print(e)
                        return None
                except KeyboardInterrupt:
                    if mp.prompt_mode in ["readline"]:
                        mp.interrupted = True
                        api.interrupts_pending(True)
                        api.check_user_interrupt()

            return text

        rsession = RSession()
        rsession.read_console = callbacks.create_read_console(result_from_prompt)
        rsession.write_console_ex = callbacks.write_console_ex
        rsession.clean_up = callbacks.clean_up
        rsession.show_message = callbacks.show_message

        # to make api work
        api.rsession = rsession

        rsession.run()
