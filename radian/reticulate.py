import os
import sys

from rchitect import rcall
from rchitect.interface import roption, set_hook, package_event

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
        def reticulate_message_hook(*args):
            if not roption("radian.suppress_reticulate_message", False):
                rcall("packageStartupMessage", RETICULATE_MESSAGE)

        set_hook(package_event("reticulate", "onLoad"), reticulate_message_hook)

    if roption("radian.enable_reticulate_prompt", True):
        def reticulate_prompt(*args):
            rcall(
                ("base", "source"),
                os.path.join(os.path.dirname(__file__), "R", "reticulate_prompt.R"),
                rcall("new.env"))

        set_hook(package_event("reticulate", "onLoad"), reticulate_prompt)