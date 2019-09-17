from __future__ import unicode_literals

import re
from rchitect.interface import roption


PROMPT = "\x1b[34mr$>\x1b[0m "
SHELL_PROMPT = "\x1b[31m#!>\x1b[0m "
BROWSE_PROMPT = "\x1b[33mBrowse[{}]>\x1b[0m "
BROWSE_PATTERN = re.compile(r"Browse\[([0-9]+)\]> $")
VI_MODE_PROMPT = "\x1b[34m[{}]\x1b[0m "
STDERR_FORMAT = "\x1b[31m{}\x1b[0m"


class RadianSettings(object):
    _settings = {}

    def __getattr__(self, key):
        return self._settings[key]

    def __setattr__(self, key, value):
        self._settings[key] = value

    def _load_setting(self, key, default):
        value = roption("radian." + key, default)
        self._settings[key] = value

    def _load_prompt(self):
        prompt = roption("radian.prompt", None)
        if not prompt:
            sys_prompt = roption("prompt")
            if sys_prompt == "> ":
                prompt = PROMPT
            else:
                prompt = sys_prompt
        self._settings["prompt"] = prompt

    def load(self):
        self._load_setting("editing_mode", "emacs")
        self._load_setting("color_scheme", "native")
        self._load_setting("auto_match", False)
        self._load_setting("auto_indentation", True)
        self._load_setting("tab_size", 4)
        self._load_setting("complete_while_typing", True)
        self._load_setting("completion_timeout", 0.05)
        self._load_setting("history_search_no_duplicates", False)
        self._load_setting("insert_new_line", True)
        self._load_setting("indent_lines", True)
        self._load_prompt()
        self._load_setting("shell_prompt", SHELL_PROMPT)
        self._load_setting("browse_prompt", BROWSE_PROMPT)
        self._load_setting("show_vi_mode_prompt", True)
        self._load_setting("vi_mode_prompt", VI_MODE_PROMPT)
        self._load_setting("stderr_format", STDERR_FORMAT)

        set_width_on_resize = roption("setWidthOnResize", True)
        self._load_setting("auto_width", set_width_on_resize)


radian_settings = RadianSettings()
