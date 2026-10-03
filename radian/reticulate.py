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

from rchitect import rcall, reticulate as rreticulate
from rchitect.interface import roption

from .console import suppress_stderr
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
from .settings import radian_settings as settings


_jedi = None
_jedi_checked = False


def _get_jedi():
    global _jedi, _jedi_checked
    if not _jedi_checked:
        _jedi_checked = True
        try:
            import jedi

            _jedi = jedi
        except ImportError:
            _jedi = None
    return _jedi


# =============================================================================
# 1. Code Tidying & Multiline Execution
# =============================================================================


def unindent(lines):
    if not lines:
        return lines
    indentation = len(lines[0]) - len(lines[0].lstrip())
    if indentation == 0:
        return lines
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

WORD_PATTERN = re.compile(
    r"(?<![a-zA-Z0-9._])([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*)$"
)

_py_lexer = None
_py_tokens_cache = (None, ())


def _tokenize_python_before_cursor(document):
    global _py_lexer, _py_tokens_cache
    text = document.text_before_cursor
    if _py_tokens_cache[0] == text:
        return _py_tokens_cache[1]
    if _py_lexer is None:
        from pygments.lexers.python import PythonLexer

        _py_lexer = PythonLexer()
    tokens = tuple(_py_lexer.get_tokens_unprocessed(text))
    _py_tokens_cache = (text, tokens)
    return tokens


def cursor_in_python_comment(document):
    if "#" not in document.current_line_before_cursor:
        return False
    from pygments.token import Comment

    tokens = _tokenize_python_before_cursor(document)
    return bool(tokens) and tokens[-1][1] in Comment


def get_reticulate_completions(document, complete_event):
    if cursor_in_python_comment(document):
        return []

    if not complete_event.completion_requested:
        word_match = WORD_PATTERN.search(document.current_line_before_cursor)
        if not word_match or len(word_match.group(1)) < settings.completion_prefix_length:
            return []

    jedi = _get_jedi()
    if jedi is None:
        return []

    try:
        with suppress_stderr():
            script = jedi.Interpreter(
                document.text,
                path="input-text",
                namespaces=[__main__.__dict__],
            )
            completions = []
            for c in script.complete(
                line=document.cursor_position_row + 1,
                column=document.cursor_position_col,
            ):
                name = str(c.name_with_symbols)
                comp = str(c.complete)
                if not comp or (
                    not complete_event.completion_requested and len(comp) == len(name)
                ):
                    continue
                completions.append(Completion(name, len(comp) - len(name)))
            return completions
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

    from pygments.lexers.python import PythonLexer

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

    @pkb.add("enter", filter=insert_mode & default_focused & preceding_text(r".*:$"))
    def _(event):
        newline(event, chars=[":"])

    input_processors = (
        [HighlightMatchingBracketProcessor()]
        if settings.highlight_matching_bracket
        else None
    )

    session.register_mode(
        "reticulate",
        is_activated=lambda s: rreticulate.py_repl_active(),
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
        completer=PythonCompleter(),
        complete_while_typing=settings.complete_while_typing,
    )


def configure(session):
    if roption("radian.enable_reticulate_prompt", True):
        rreticulate.on_load(lambda: register_reticulate_mode(session))

        has_reticulate = Condition(
            lambda: "reticulate" not in session.modes and rreticulate.is_installed()
        )
        kb = session.modes["r"].prompt_key_bindings
        browsekb = session.modes["browse"].prompt_key_bindings
        tilde_filter = insert_mode & default_focused & cursor_at_begin & text_is_empty & has_reticulate

        @kb.add('~', filter=tilde_filter)
        def _activate_reticulate(event):
            commit_text(session, event, "reticulate::repl_python()", False)

        if browsekb is not kb:
            browsekb.add('~', filter=tilde_filter)(_activate_reticulate)


