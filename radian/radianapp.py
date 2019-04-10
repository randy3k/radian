from __future__ import unicode_literals
import os
import sys
import subprocess


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

        doc_dir = os.path.join(self.r_home, "doc")
        include_dir = os.path.join(self.r_home, "include")
        share_dir = os.path.join(self.r_home, "share")
        if not (os.path.isdir(doc_dir) and os.path.isdir(include_dir) and os.path.isdir(share_dir)):
            try:
                paths = subprocess.check_output([
                    os.path.join(self.r_home, "bin", "R"), "--slave", "-e",
                    "cat(paste(R.home('doc'), R.home('include'), R.home('share'), sep=':'))"
                ])
                doc_dir, include_dir, share_dir = paths.decode().split(":")
            except Exception:
                pass

        os.environ["R_DOC_DIR"] = doc_dir
        os.environ["R_INCLUDE_DIR"] = include_dir
        os.environ["R_SHARE_DIR"] = share_dir

    def run(self, options):
        from .prompt import create_radian_prompt_session, register_modes
        from .read_console import create_read_console
        import rchitect

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

        rchitect.setup.def_callback(name="read_console")(create_read_console(session))
        rchitect.init(args=args)

        # TODO: refactor session_initialize and register_modes
        self.session_initialize(session)
        register_modes(session)

        # print welcome message
        if options.quiet is not True:
            session.app.output.write(rchitect.interface.greeting())

        rchitect.loop()

    def session_initialize(self, session):
        from rchitect import rcopy, reval
        from rchitect.interface import roption, setoption
        from prompt_toolkit.enums import EditingMode
        from prompt_toolkit.styles import style_from_pygments_cls
        from pygments.styles import get_style_by_name

        from .prompt import PROMPT, BROWSE_PROMPT, SHELL_PROMPT

        # if not sys.platform.startswith("win"):
        #     def reticulate_hook(*args):
        #         rcall(
        #             ("base", "source"),
        #             os.path.join(os.path.dirname(__file__), "data", "patching_reticulate.R"),
        #             new_env())

        #     set_hook(package_event("reticulate", "onLoad"), reticulate_hook)

        # if not roption("radian.suppress_reticulate_message", False):
        #     def reticulate_message_hook(*args):
        #         if not roption("radian.suppress_reticulate_message", False):
        #             rcall("packageStartupMessage", RETICULATE_MESSAGE)

        #     set_hook(package_event("reticulate", "onLoad"), reticulate_message_hook)

        # if roption("radian.enable_reticulate_prompt", True):
        #     def reticulate_prompt(*args):
        #         rcall(
        #             ("base", "source"),
        #             os.path.join(os.path.dirname(__file__), "data", "register_reticulate.R"),
        #             new_env())

        #     set_hook(package_event("reticulate", "onLoad"), reticulate_prompt)

        if roption("radian.editing_mode", "emacs") in ["vim", "vi"]:
            session.app.editing_mode = EditingMode.VI
        else:
            session.app.editing_mode = EditingMode.EMACS

        color_scheme = roption("radian.color_scheme", "native")
        session.style = style_from_pygments_cls(get_style_by_name(color_scheme))

        session.auto_match = roption("radian.auto_match", False)
        session.auto_indentation = roption("radian.auto_indentation", True)
        session.tab_size = int(roption("radian.tab_size", 4))
        session.complete_while_typing = roption("radian.complete_while_typing", True)
        session.completion_timeout = roption("radian.completion_timeout", 0.05)

        session.history_search_no_duplicates = roption("radian.history_search_no_duplicates", False)
        session.insert_new_line = roption("radian.insert_new_line", True)
        session.indent_lines = roption("radian.indent_lines", True)

        prompt = roption("radian.prompt", None)
        if not prompt:
            sys_prompt = roption("prompt")
            if sys_prompt == "> ":
                prompt = PROMPT
            else:
                prompt = sys_prompt

        session.default_prompt = prompt
        setoption("prompt", prompt)

        shell_prompt = roption("radian.shell_prompt", SHELL_PROMPT)
        session.shell_prompt = shell_prompt

        browse_prompt = roption("radian.browse_prompt", BROWSE_PROMPT)
        session.browse_prompt = browse_prompt

        set_width_on_resize = roption("setWidthOnResize", True)
        session.auto_width = roption("radian.auto_width", set_width_on_resize)
        output_width = session.app.output.get_size().columns
        if output_width and session.auto_width:
            setoption("width", output_width)

        # necessary on windows
        setoption("menu.graphics", False)

        # enables completion of installed package names
        if rcopy(reval("rc.settings('ipck')")) is None:
            reval("rc.settings(ipck = TRUE)")

        # backup the updated settings
        session._backup_settings()
