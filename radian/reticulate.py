from __future__ import unicode_literals
import os
import sys
from code import compile_command

from rchitect import rcall, rcopy
from rchitect.interface import roption, setoption, set_hook, package_event

from .rutils import package_is_installed

from .key_bindings import insert_mode, default_focussed, cursor_at_begin, text_is_empty
from .key_bindings import commit_text
from . import get_app


try:
    import jedi
except ImportError:
    pass


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

        session = get_app().session
        kb = session.modes["r"].prompt_key_bindings
        browsekb = session.modes["browse"].prompt_key_bindings

        @kb.add('~', filter=insert_mode & default_focussed & cursor_at_begin & text_is_empty)
        @browsekb.add('~', filter=insert_mode & default_focussed & cursor_at_begin & text_is_empty)
        def _(event):
            setoption("radian.suppress_reticulate_message", True)
            commit_text(event, "reticulate::repl_python()", False)


def reticulate_message_hook(*args):
    if not roption("radian.suppress_reticulate_message", False):
        rcall("packageStartupMessage", RETICULATE_MESSAGE)


def reticulate_prompt_hook(*args):
    rcall(
        ("base", "source"),
        os.path.join(os.path.dirname(__file__), "R", "reticulate.R"),
        rcall("new.env"))


def prase_text_complete(code):
    if "\n" in code:
        try:
            return compile_command(code, "<input>", "exec") is not None
        except Exception:
            return True
    else:
        if len(code.strip()) == 0:
            return True
        elif code[0] == "?" or code[-1] == "?":
            return True
        else:
            try:
                return compile_command(code, "<input>", "single") is not None
            except Exception:
                return True


def get_reticulate_completions(document, complete_event):
    word = document.get_word_before_cursor()
    if len(word) < 3 and not complete_event.completion_requested:
        return []

    glo = rcopy(rcall(("reticulate", "py_run_string"), "globals()"))
    loc = rcopy(rcall(("reticulate", "py_run_string"), "locals()"))
    try:
        script = jedi.Interpreter(
            document.text,
            column=document.cursor_position_col,
            line=document.cursor_position_row + 1,
            path="input-text",
            namespaces=[glo, loc]
        )
    except Exception:
        script = None

    if not script:
        return []

    return list(script.completions())
