import __main__
import ast
from code import compile_command
import re
import sys

from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.key_binding.key_bindings import KeyBindings
from prompt_toolkit.layout.processors import HighlightMatchingBracketProcessor
from prompt_toolkit.lexers import PygmentsLexer
from pygments.lexers.python import PythonLexer

from rchitect import rcall, rcopy, reval
from rchitect.interface import roption, set_hook, package_event

from radian import get_app
from radian.key_bindings import (
    commit_text,
    create_prompt_key_bindings,
    cursor_at_begin,
    default_focused,
    insert_mode,
    newline,
    preceding_text,
    prompt_mode,
    text_is_empty,
)
from radian.latex import get_latex_completions
from radian.rutils import package_is_installed
from radian.settings import radian_settings as settings


try:
    import jedi
    has_jedi = True
except ImportError:
    has_jedi = False


def leading_spaces(x):
    m = re.match(r"^\s*", x)
    return m.group(0) if m else ""


def unindent(lines):
    if not lines:
        return lines
    indentation = len(leading_spaces(lines[0]))
    pattern = re.compile(r"^\s{{0,{}}}".format(indentation))
    return [pattern.sub("", line, count=1) for line in lines]


def tidy_code(code):
    code = code.replace("\r", "").rstrip()
    lines = unindent(code.split("\n"))
    return "\n".join(lines)


def handle_multiline_code(code):
    main_dict = __main__.__dict__
    try:
        mod = ast.parse(code, "<input>", "exec")
        if mod.body and isinstance(mod.body[-1], ast.Expr):
            if len(mod.body) > 1:
                prefix = ast.Module(body=mod.body[:-1], type_ignores=[])
                eval(compile(prefix, "<input>", "exec"), main_dict, main_dict)
            last = ast.Interactive(body=[mod.body[-1]])
            eval(compile(last, "<input>", "single"), main_dict, main_dict)
        else:
            eval(compile(mod, "<input>", "exec"), main_dict, main_dict)
    except Exception as e:
        sys.last_type, sys.last_value, sys.last_traceback = sys.exc_info()
        rcall(("base", "message"), "{}: {}".format(type(e).__name__, e))


def handle_code(code):
    code = tidy_code(code)
    if "\n" in code:
        # reticulate repl doesn't handle multiline code, execute it directly in Python
        handle_multiline_code(code)
        return None
    return code


def parse_text_complete(code):
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


if has_jedi and tuple(int(x) for x in jedi.__version__.split(".")[0:2]) >= (0, 18):
    def get_reticulate_completions(document, complete_event):
        word = document.get_word_before_cursor()
        prefix_length = settings.completion_prefix_length
        if len(word) < prefix_length and not complete_event.completion_requested:
            return []

        try:
            script = jedi.Interpreter(
                document.text,
                path="input-text",
                namespaces=[__main__.__dict__]
            )
            return [
                Completion(
                    str(c.name_with_symbols),
                    len(str(c.complete)) - len(str(c.name_with_symbols)))
                for c in script.complete(
                    line=document.cursor_position_row + 1, column=document.cursor_position_col)
            ]
        except Exception:
            return []
else:
    def get_reticulate_completions(document, complete_event):
        word = document.get_word_before_cursor()
        prefix_length = settings.completion_prefix_length
        if len(word) < prefix_length and not complete_event.completion_requested:
            return []

        try:
            script = jedi.Interpreter(
                document.text,
                column=document.cursor_position_col,
                line=document.cursor_position_row + 1,
                path="input-text",
                namespaces=[__main__.__dict__]
            )
            return [
                Completion(
                    str(c.name_with_symbols),
                    len(str(c.complete)) - len(str(c.name_with_symbols)))
                for c in script.completions()
            ]
        except Exception:
            return []


class PythonCompleter(Completer):
    def get_completions(self, document, complete_event):
        latex_comps = get_latex_completions(document, complete_event)
        if len(latex_comps) > 0:
            return latex_comps
        return get_reticulate_completions(document, complete_event)


def register_reticulate_mode(*args):
    app = get_app()
    if not app or "reticulate" in app.session.modes:
        return

    main_mode = prompt_mode("r") | prompt_mode("browse")
    kb = KeyBindings()

    @kb.add("~", filter=main_mode & insert_mode & default_focused & cursor_at_begin & text_is_empty)
    def _(event):
        commit_text(event, "reticulate::repl_python(quiet = TRUE)", False)

    pkb = create_prompt_key_bindings(parse_text_complete)

    @pkb.add("c-d", filter=insert_mode & default_focused & cursor_at_begin & text_is_empty)
    @pkb.add("backspace", filter=insert_mode & default_focused & cursor_at_begin & text_is_empty)
    def _(event):
        commit_text(event, "exit", False)

    @pkb.add("enter", filter=insert_mode & default_focused & preceding_text(".*:"))
    def _(event):
        newline(event, chars=[":"])

    python_completer = PythonCompleter() if has_jedi else None
    input_processors = (
        [HighlightMatchingBracketProcessor()]
        if settings.highlight_matching_bracket
        else None
    )

    py_repl_active = reval("reticulate:::py_repl_active")

    app.session.register_mode(
        "reticulate",
        is_activated=lambda session: bool(rcall(py_repl_active, _convert=True)),
        prompt_message=lambda x: x,
        callback=lambda session: handle_code(session.default_buffer.text),
        multiline=True,
        insert_new_line=True,
        insert_new_line_on_sigint=True,
        lexer=PygmentsLexer(PythonLexer),
        key_bindings=kb,
        prompt_key_bindings=pkb,
        tempfile_suffix=".py",
        input_processors=input_processors,
        completer=python_completer,
    )


def configure():
    if package_is_installed("reticulate") and roption("radian.enable_reticulate_prompt", True):
        if "reticulate" in rcall(("base", "loadedNamespaces"), _convert=True):
            register_reticulate_mode()
        else:
            set_hook(package_event("reticulate", "onLoad"), register_reticulate_mode)

        session = get_app().session
        kb = session.modes["r"].prompt_key_bindings
        browsekb = session.modes["browse"].prompt_key_bindings

        @kb.add('~', filter=insert_mode & default_focused & cursor_at_begin & text_is_empty)
        @browsekb.add('~', filter=insert_mode & default_focused & cursor_at_begin & text_is_empty)
        def _(event):
            commit_text(event, "reticulate::repl_python()", False)
