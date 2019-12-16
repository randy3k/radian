from __future__ import unicode_literals
from prompt_toolkit.completion import Completer, Completion
import os
import sys
import shlex
import re

from rchitect import completion as rcompletion
from .rutils import installed_packages
from .latex import latex_symbols

from six import text_type


TOKEN_PATTERN = re.compile(r".*?([a-zA_Z0-9._]+)$")
LATEX_PATTERN = re.compile(r".*?(\\[a-zA_Z0-9^_]+)$")
LIBRARY_PATTERN = re.compile(r"(?:library|require)\([\"']?(.*)$")


class RCompleter(Completer):
    initialized = False

    def __init__(self, timeout=0.02):
        self.timeout = timeout
        super(RCompleter, self).__init__()

    def get_completions(self, document, complete_event):
        text_before = document.current_line_before_cursor
        text_after = document.text_after_cursor
        completion_requested = complete_event.completion_requested

        latex_comps = list(self.latex_completion(text_before, text_after, completion_requested))
        if len(latex_comps) > 0:
            for x in latex_comps:
                yield x
            # only return latex completions if prefix has \
            return

        for x in self.r_completion(text_before, text_after, completion_requested):
            yield x
        for x in self.package_completion(text_before, text_after, completion_requested):
            yield x

    def r_completion(self, text_before, text_after, completion_requested):
        orig_stderr = sys.stderr
        sys.stderr = None
        try:
            token = rcompletion.assign_line_buffer(text_before)
            rcompletion.complete_token(0 if completion_requested else self.timeout)
            completions = rcompletion.retrieve_completions()
        except Exception:
            completions = []
        finally:
            sys.stderr = orig_stderr

        for c in completions:
            if c.startswith(token):
                if c.endswith("="):
                    c = c[:-1] + " = "
                if c.endswith("::"):
                    # let package_completion handles it
                    continue
                yield Completion(c, -len(token))

    def package_completion(self, text_before, text_after, completion_requested):
        token_match = TOKEN_PATTERN.match(text_before)
        library_prefix = LIBRARY_PATTERN.match(text_before)
        if token_match and not library_prefix:
            token = token_match.group(1)
            instring = text_after.startswith("'") or text_after.startswith('"')
            for p in installed_packages():
                if p.startswith(token):
                    comp = p if instring else p + "::"
                    yield Completion(comp, -len(token))

    def latex_completion(self, text_before, text_after, completion_requested):
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


class SmartPathCompleter(Completer):
    def get_completions(self, document, complete_event):
        text = document.text_before_cursor
        if len(text) == 0:
            return

        # do not auto complete when typing
        if not complete_event.completion_requested:
            return

        if sys.platform.startswith('win'):
            text = text.replace("\\", "/")

        directories_only = False
        quoted = False

        if text.lstrip().startswith("cd "):
            directories_only = True
            text = text.lstrip()[3:]

        try:
            path = ""
            while not path and text:
                quoted = False
                try:
                    if text.startswith('"'):
                        path = shlex.split(text + "\"")[-1]
                        quoted = True
                    elif text.startswith("'"):
                        path = shlex.split(text + "'")[-1]
                        quoted = True
                    else:
                        path = shlex.split(text)[-1]
                except RuntimeError:
                    pass
                finally:
                    if not path:
                        text = text[1:]

            path = os.path.expanduser(path)
            path = os.path.expandvars(path)
            if not os.path.isabs(path):
                path = os.path.join(os.getcwd(), path)
            basename = os.path.basename(path)
            dirname = os.path.dirname(path)

            for c in os.listdir(dirname):
                if directories_only and not os.path.isdir(os.path.join(dirname, c)):
                    continue
                if c.lower().startswith(basename.lower()):
                    if sys.platform.startswith('win') or quoted:
                        yield Completion(text_type(c), -len(basename))
                    else:
                        yield Completion(text_type(c.replace(" ", "\\ ")), -len(basename))

        except Exception:
            pass
