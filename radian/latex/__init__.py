import re
from prompt_toolkit.completion import Completion

from .latex_symbols import latex_symbols

__all__ = ["latex_symbols"]


LATEX_PATTERN = re.compile(r".*?(\\[a-zA-Z0-9^_]+)$")


def _get_latex_completions(document, complete_event):
    text_before = document.current_line_before_cursor
    latex_match = LATEX_PATTERN.match(text_before)
    if latex_match:
        token = latex_match.group(1)
        exact_match_found = False
        for command, sym in latex_symbols:
            if command == token:
                exact_match_found = True
                yield Completion(sym, -len(token), display=command, display_meta=sym)
                break
        for command, sym in latex_symbols:
            if command.startswith(token) and not (exact_match_found and command == token):
                yield Completion(sym, -len(token), display=command, display_meta=sym)


def get_latex_completions(document, complete_event):
    return list(_get_latex_completions(document, complete_event))
