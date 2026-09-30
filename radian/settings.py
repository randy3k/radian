from rchitect.interface import roption


PROMPT = "\x1b[34mr$>\x1b[0m "
SHELL_PROMPT = "\x1b[31m#!>\x1b[0m "
BROWSE_PROMPT = "\x1b[33mBrowse[{}]>\x1b[0m "
VI_MODE_PROMPT = "\x1b[34m[{}]\x1b[0m "
STDERR_FORMAT = "\x1b[31m{}\x1b[0m"


_DEFAULT_SETTINGS = (
    ("auto_suggest", False, bool),
    ("emacs_bindings_in_vi_insert_mode", False, bool),
    ("editing_mode", "emacs", None),
    ("color_scheme", "native", None),
    ("auto_match", True, bool),
    ("highlight_matching_bracket", False, bool),
    ("auto_indentation", True, bool),
    ("tab_size", 4, int),
    ("complete_while_typing", True, bool),
    ("completion_timeout", 0.15, None),
    ("completion_prefix_length", 2, int),
    ("completion_adding_spaces_around_equals", True, bool),
    ("history_size", 20000, int),
    ("global_history_file", "~/.radian_history", None),
    ("local_history_file", ".radian_history", None),
    ("history_search_no_duplicates", False, bool),
    ("history_search_ignore_case", False, bool),
    ("history_ignore_browser_commands", True, bool),
    ("insert_new_line", True, bool),
    ("indent_lines", True, bool),
    ("shell_prompt", SHELL_PROMPT, None),
    ("browse_prompt", BROWSE_PROMPT, None),
    ("show_vi_mode_prompt", True, bool),
    ("vi_mode_prompt", VI_MODE_PROMPT, None),
    ("stderr_format", STDERR_FORMAT, None),
)


class RadianSettings:
    def __init__(self):
        super().__setattr__("_settings", {})

    def __getattr__(self, key):
        return self._settings[key]

    def __setattr__(self, key, value):
        self._settings[key] = value

    def _load_setting(self, key, default, coercion=None):
        value = roption("radian." + key, default)
        self._settings[key] = coercion(value) if coercion else value

    def _load_prompt(self):
        prompt = roption("radian.prompt", None)
        if not prompt:
            sys_prompt = roption("prompt")
            prompt = PROMPT if sys_prompt == "> " else sys_prompt
        self._settings["prompt"] = prompt

    def load(self):
        for key, default, coercion in _DEFAULT_SETTINGS:
            self._load_setting(key, default, coercion)
        self._load_prompt()
        set_width_on_resize = roption("setWidthOnResize", True)
        self._load_setting("auto_width", set_width_on_resize, bool)


radian_settings = RadianSettings()

