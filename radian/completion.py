from __future__ import unicode_literals
from prompt_toolkit.completion import Completer, Completion
import os
import sys
import shlex
import re

from rchitect.interface import rcall, reval, rcopy, rstring, rint

from six import text_type


LIBRARY_PATTERN = re.compile(r"(?:library|require)\([\"']?(.*)$")

CompleteCode = """
local(suppressWarnings({{tryCatch(
    {{
        if ({settimelimit}) base::setTimeLimit({timeout})
        utils:::.completeToken()
        if ({settimelimit}) base::setTimeLimit()
    }},
    error = function(e) {{
        if ({settimelimit}) base::setTimeLimit()
        assign("comps", NULL, env = utils:::.CompletionEnv)
    }}
)}}))
"""


class RCompleter(Completer):
    initialized = False

    def __init__(self, timeout=0.02):
        self.timeout = timeout
        super(RCompleter, self).__init__()

    def get_completions(self, document, complete_event):
        token = ""
        text = document.current_line_before_cursor
        text_after = document.text_after_cursor

        completions = []
        rcall(reval("utils:::.assignLinebuffer"), rstring(text))
        rcall(reval("utils:::.assignEnd"), rint(len(text)))
        token = rcopy(text_type, rcall(reval("utils:::.guessTokenFromLine")))
        completion_requested = complete_event.completion_requested
        completions = []

        if (len(token) >= 3 and text[-1].isalnum()) or completion_requested:
            orig_stderr = sys.stderr
            sys.stderr = None
            try:
                reval(CompleteCode.format(
                    settimelimit="TRUE" if not completion_requested and self.timeout > 0 else "FALSE",
                    timeout=str(self.timeout)))
            except Exception:
                return
            finally:
                sys.stderr = orig_stderr

            completions = rcopy(list, rcall(reval("utils:::.retrieveCompletions")))
            if not completions:
                completions = []

        for c in completions:
            if c.startswith(token):
                yield Completion(c, -len(token))

        library_prefix = LIBRARY_PATTERN.match(text)
        if token and not library_prefix:
            if (len(token) >= 3 and text[-1].isalnum()) or completion_requested:
                instring = text_after.startswith("'") or text_after.startswith('"')
                packages = rcopy(list, reval("""
                    tryCatch(
                        base::rownames(utils::installed.packages()),
                        error = function(e) character(0)
                    )
                    """))
                for p in packages:
                    if p.startswith(token):
                        comp = p if instring else p + "::"
                        if comp not in completions:
                            yield Completion(comp, -len(token))


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
