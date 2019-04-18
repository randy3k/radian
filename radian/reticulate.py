import os
import sys

from rchitect import rcall
from rchitect.interface import roption, setoption, set_hook, package_event

from .rutils import package_is_installed


RETICULATE_MESSAGE = """
The host python environment is {}
and `radian` is forcing `reticulate` to use this version of python.
Any python packages needed, e.g., `tensorflow` and `keras`,
have to be available to the current python environment.

File an issue at https://github.com/randy3k/radian if you encounter any
difficulties in loading `reticulate`.
""".format(sys.executable).strip()


def hooks():
    if not roption("radian.suppress_reticulate_message", False):
        set_hook(package_event("reticulate", "onLoad"), reticulate_message_hook)

    if package_is_installed("reticulate") and roption("radian.enable_reticulate_prompt", True):
        set_hook(package_event("reticulate", "onLoad"), reticulate_prompt_hook)
        from .keybindings import insert_mode, default_focussed, cursor_at_begin, text_is_empty
        from .keybindings import commit_text
        from . import get_app

        session = get_app().session
        kb = session.modes["r"].prompt_key_bindings

        @kb.add('~', filter=insert_mode & default_focussed & cursor_at_begin & text_is_empty)
        def _(event):
            setoption("radian.suppress_reticulate_message", True)
            commit_text(event, "reticulate::repl_python()", False)
            # remove itself
            kb.remove(_)


def reticulate_message_hook(*args):
    if not roption("radian.suppress_reticulate_message", False):
        rcall("packageStartupMessage", RETICULATE_MESSAGE)


def reticulate_prompt_hook(*args):
    rcall(
        ("base", "source"),
        os.path.join(os.path.dirname(__file__), "R", "reticulate_prompt.R"),
        rcall("new.env"))
