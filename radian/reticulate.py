import __main__
import ast
from code import compile_command
import re
import sys

from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.filters import Condition
from prompt_toolkit.key_binding.key_bindings import KeyBindings
from prompt_toolkit.layout.processors import HighlightMatchingBracketProcessor
from prompt_toolkit.lexers import PygmentsLexer
from pygments.lexers.python import PythonLexer

from rchitect import rcall, reval
from rchitect.interface import package_event, roption, set_hook

from .key_bindings import (
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
from .latex import get_latex_completions
from .rutils import package_is_installed, package_is_loaded
from .settings import radian_settings as settings


try:
    import jedi
    has_jedi = True
except ImportError:
    has_jedi = False


# =============================================================================
# 1. Code Tidying & Multiline Execution
# =============================================================================

LEADING_SPACES_RE = re.compile(r"^\s*")


def leading_spaces(x):
    m = LEADING_SPACES_RE.match(x)
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


# =============================================================================
# 2. Completion (Jedi & LaTeX)
# =============================================================================


def get_reticulate_completions(document, complete_event):
    word = document.get_word_before_cursor()
    prefix_length = settings.completion_prefix_length
    if len(word) < prefix_length and not complete_event.completion_requested:
        return []

    try:
        script = jedi.Interpreter(
            document.text,
            path="input-text",
            namespaces=[__main__.__dict__],
        )
        return [
            Completion(
                str(c.name_with_symbols),
                len(str(c.complete)) - len(str(c.name_with_symbols)),
            )
            for c in script.complete(
                line=document.cursor_position_row + 1,
                column=document.cursor_position_col,
            )
        ]
    except Exception:
        return []


class PythonCompleter(Completer):
    def get_completions(self, document, complete_event):
        latex_comps = get_latex_completions(document, complete_event)
        if latex_comps:
            return latex_comps
        return get_reticulate_completions(document, complete_event)


# =============================================================================
# 3. Reticulate Mode Registration & Configuration
# =============================================================================


def register_reticulate_mode(session):
    if "reticulate" in session.modes:
        return

    main_mode = prompt_mode(session, "r") | prompt_mode(session, "browse")
    kb = KeyBindings()

    @kb.add("~", filter=main_mode & insert_mode & default_focused & cursor_at_begin & text_is_empty)
    def _(event):
        commit_text(session, event, "reticulate::repl_python(quiet = TRUE)", False)

    pkb = create_prompt_key_bindings(parse_text_complete)

    @pkb.add("c-d", filter=insert_mode & default_focused & cursor_at_begin & text_is_empty)
    @pkb.add("backspace", filter=insert_mode & default_focused & cursor_at_begin & text_is_empty)
    def _(event):
        commit_text(session, event, "exit", False)

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

    session.register_mode(
        "reticulate",
        is_activated=lambda s: bool(rcall(py_repl_active, _convert=True)),
        prompt_message=lambda x: x,
        callback=lambda s: handle_code(s.default_buffer.text),
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


def configure(session):
    if roption("radian.enable_reticulate_prompt", True):
        if package_is_loaded("reticulate"):
            register_reticulate_mode(session)
        else:
            set_hook(
                package_event("reticulate", "onLoad"),
                lambda *args: register_reticulate_mode(session),
            )

        has_reticulate = Condition(lambda: package_is_installed("reticulate"))
        kb = session.modes["r"].prompt_key_bindings
        browsekb = session.modes["browse"].prompt_key_bindings

        @kb.add('~', filter=insert_mode & default_focused & cursor_at_begin & text_is_empty & has_reticulate)
        @browsekb.add('~', filter=insert_mode & default_focused & cursor_at_begin & text_is_empty & has_reticulate)
        def _(event):
            commit_text(session, event, "reticulate::repl_python()", False)


