from __future__ import unicode_literals
from prompt_toolkit.application.current import get_app
from prompt_toolkit.completion import Completer, Completion
import re

from . import api
from . import interface


LIBRARY_PATTERN = re.compile(r"(?:library|require)\([\"']?(.*)$")


class RCompleter(Completer):
    _methods_exist = False

    def get_utils_func(self, fname):
        f = interface.rlang(api.mk_symbol(":::"), api.mk_string("utils"), api.mk_string(fname))
        api.preserve_object(f)
        return f

    def _make_sure_methods_exist(self):
        if not self._methods_exist:
            self.assignLinebuffer = self.get_utils_func(".assignLinebuffer")
            self.assignEnd = self.get_utils_func(".assignEnd")
            self.guessTokenFromLine = self.get_utils_func(".guessTokenFromLine")
            self.completeToken = self.get_utils_func(".completeToken")
            self.retrieveCompletions = self.get_utils_func(".retrieveCompletions")
            self._methods_exist = True

    def get_completions(self, document, complete_event):
        self._make_sure_methods_exist()
        token = ""
        app = get_app(return_none=True)
        if app and hasattr(app, "prompt_mode") and app.prompt_mode in ["r", "help"]:

            packages = interface.installed_packages()
            text = document.current_line_before_cursor
            m = LIBRARY_PATTERN.match(text)
            if m:
                prefix = m.group(1)
                for p in packages:
                    if p.startswith(prefix):
                        yield Completion(p, -len(prefix))

            else:
                completions = []
                s = api.protect(api.mk_string(text))
                interface.rcall(self.assignLinebuffer, s)
                interface.rcall(self.assignEnd, api.scalar_integer(len(text)))
                token = interface.rcopy(interface.rcall(self.guessTokenFromLine))[0]
                if (len(token) > 3 and text[-1].isalnum()) or complete_event.completion_requested:
                    interface.rcall(self.completeToken)
                    completions = interface.rcopy(interface.rcall(self.retrieveCompletions))
                api.unprotect(1)

                for c in completions:
                    yield Completion(c, -len(token))

                if len(token) >= 3:
                    for p in packages:
                        if p.startswith(token):
                            comp = p + "::"
                            if comp not in completions:
                                yield Completion(comp, -len(token))
