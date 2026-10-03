import re
from prompt_toolkit.completion import Completion
from ..settings import radian_settings as settings

__all__ = ["latex_symbols"]


LATEX_PATTERN = re.compile(r"(\\[a-zA-Z0-9^_]+)$")

_LATEX_EXACT = None
_LATEX_BY_PREFIX2 = None


def _ensure_latex_index():
    global _LATEX_EXACT, _LATEX_BY_PREFIX2
    if _LATEX_EXACT is None:
        from .latex_symbols import latex_symbols

        _LATEX_EXACT = dict(latex_symbols)
        _LATEX_BY_PREFIX2 = {}
        for cmd, sym in latex_symbols:
            _LATEX_BY_PREFIX2.setdefault(cmd[:2], []).append((cmd, sym))


def __getattr__(name):
    if name == "latex_symbols":
        from .latex_symbols import latex_symbols

        return latex_symbols
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def _get_latex_completions(document, complete_event):
    text_before = document.current_line_before_cursor
    if "\\" not in text_before:
        return
    latex_match = LATEX_PATTERN.search(text_before)
    if latex_match:
        token = latex_match.group(1)
        if (
            not complete_event.completion_requested
            and len(token) - 1 < settings.completion_prefix_length
        ):
            return
        _ensure_latex_index()
        exact_sym = _LATEX_EXACT.get(token)
        if exact_sym is not None:
            yield Completion(exact_sym, -len(token), display=token, display_meta=exact_sym)
        for command, sym in _LATEX_BY_PREFIX2.get(token[:2], ()):
            if command.startswith(token) and command != token:
                yield Completion(sym, -len(token), display=command, display_meta=sym)


def get_latex_completions(document, complete_event):
    return list(_get_latex_completions(document, complete_event))

