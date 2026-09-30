from prompt_toolkit.completion import Completer, Completion
import os
import sys
import shlex
import re

from rchitect import completion as rcompletion

from .settings import radian_settings as settings
from .latex import get_latex_completions
from .rutils import installed_packages
from .console import suppress_stderr
from .lexer import cursor_in_string



TOKEN_PATTERN = re.compile(r"(?<![:$@a-zA-Z0-9._])([a-zA-Z0-9._]+)$")
LIBRARY_PATTERN = re.compile(
    r"(?<![a-zA-Z0-9._])(?:(?:library|require)\([\"']?|requireNamespace\([\"'])([a-zA-Z0-9._]*)$"
)
NESTED_PAREN_PATTERN = re.compile(r"\([^())]*\)")
PRINT_PATTERN = re.compile(r"print\([^\)]*$")


def remove_nested_paren(text):
    new_text = NESTED_PAREN_PATTERN.sub("", text)
    while new_text != text:
        text = new_text
        new_text = NESTED_PAREN_PATTERN.sub("", text)
    return text


class RCompleter(Completer):
    def __init__(self, timeout=0.02):
        self.timeout = timeout
        super().__init__()

    def get_completions(self, document, complete_event):
        word = document.get_word_before_cursor()
        prefix_length = settings.completion_prefix_length
        if len(word) < prefix_length and not complete_event.completion_requested:
            return

        latex_comps = get_latex_completions(document, complete_event)
        # only return latex completions if prefix has \
        if latex_comps:
            yield from latex_comps
            return

        yield from self.get_r_builtin_completions(document, complete_event)
        yield from self.get_package_completions(document, complete_event)

    def get_r_builtin_completions(self, document, complete_event):
        text_before = document.current_line_before_cursor
        completion_requested = complete_event.completion_requested

        library_prefix = LIBRARY_PATTERN.search(text_before)
        if library_prefix:
            return

        with suppress_stderr():
            try:
                # Completion while typing inside "print(" is slow because R's
                # utils:::.completeToken() calls functionArgs("print", ...), which
                # inspects all S3 methods of print(). First call assign_line_buffer
                # on the full line to extract the token, then overwrite R's
                # .CompletionEnv$linebuffer with just `token` on the second call
                # so inFunction() does not see "print(".
                if (
                    not completion_requested
                    and "print(" in text_before
                    and PRINT_PATTERN.search(remove_nested_paren(text_before))
                ):
                    text_before = rcompletion.assign_line_buffer(text_before)

                token = rcompletion.assign_line_buffer(text_before)
                # do not timeout package::func
                if "::" in token or completion_requested:
                    timeout = 0
                else:
                    timeout = self.timeout
                rcompletion.complete_token(timeout)
                completions = rcompletion.retrieve_completions()
            except Exception:
                completions = []

        for c in completions:
            if c.startswith(token) and c != token:
                if c.endswith("=") and settings.completion_adding_spaces_around_equals:
                    c = c[:-1] + " = "
                if c.endswith("::"):
                    # let get_package_completions handles it
                    continue
                yield Completion(c, -len(token))

    def get_package_completions(self, document, complete_event):
        text_before = document.current_line_before_cursor
        token_match = TOKEN_PATTERN.search(text_before)
        if not token_match:
            return
        token = token_match.group(1)
        library_prefix = LIBRARY_PATTERN.search(text_before)
        if not library_prefix and cursor_in_string(document):
            return
        for p in installed_packages():
            if p.startswith(token):
                comp = p if library_prefix else p + "::"
                yield Completion(comp, -len(token))


class SmartPathCompleter(Completer):
    def get_completions(self, document, complete_event):
        text = document.text_before_cursor
        if len(text) == 0:
            return

        # do not auto complete when typing
        if not complete_event.completion_requested:
            return

        is_win = sys.platform.startswith("win")
        if is_win:
            text = text.replace("\\", "/")

        directories_only = False
        quoted = False

        stripped = text.lstrip()
        if stripped.startswith("cd "):
            directories_only = True
            text = stripped[3:]

        try:
            path = ""
            while not path and text:
                quoted = False
                try:
                    if text.startswith('"'):
                        path = shlex.split(text + '"')[-1]
                        quoted = True
                    elif text.startswith("'"):
                        path = shlex.split(text + "'")[-1]
                        quoted = True
                    else:
                        path = shlex.split(text)[-1]
                except (RuntimeError, ValueError, IndexError):
                    pass
                finally:
                    if not path:
                        text = text[1:]

            path = os.path.expanduser(path)
            path = os.path.expandvars(path)
            if not os.path.isabs(path):
                path = os.path.join(os.getcwd(), path)
            basename = os.path.basename(path)
            basename_lower = basename.lower()
            dirname = os.path.dirname(path)

            for c in os.listdir(dirname):
                if not c.lower().startswith(basename_lower):
                    continue
                if directories_only and not os.path.isdir(os.path.join(dirname, c)):
                    continue
                if is_win or quoted:
                    yield Completion(str(c), -len(basename))
                else:
                    yield Completion(str(c.replace(" ", "\\ ")), -len(basename))

        except Exception:
            pass

