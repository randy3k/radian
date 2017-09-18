from __future__ import unicode_literals
from prompt_toolkit.application.current import get_app
from prompt_toolkit.completion import Completer, Completion
import os
import re
import sys
import shlex

from . import api
from . import interface

from six import text_type


LIBRARY_PATTERN = re.compile(r"(?:library|require)\([\"']?(.*)$")


class ModalPromptCompleter(Completer):
    def __init__(self, *args, **kwargs):
        super(ModalPromptCompleter, self).__init__(*args, **kwargs)
        self.rcompleter = RCompleter()
        self.path_completer = SmartPathCompleter()

    def get_completions(self, document, complete_event):
        app = get_app(return_none=True)
        if app and hasattr(app, "mp"):
            if app.mp.prompt_mode in ["r", "help", "help_search"]:
                for c in self.rcompleter.get_completions(document, complete_event):
                    yield c
            elif app.mp.prompt_mode == "shell":
                for c in self.path_completer.get_completions(document, complete_event):
                    yield c


class RCompleter(Completer):
    initialized = False

    def get_utils_func(self, fname):
        f = interface.rlang(api.mk_symbol(":::"), api.mk_string("utils"), api.mk_string(fname))
        api.preserve_object(f)
        return f

    def initialize(self):
        self.assignLinebuffer = self.get_utils_func(".assignLinebuffer")
        self.assignEnd = self.get_utils_func(".assignEnd")
        self.guessTokenFromLine = self.get_utils_func(".guessTokenFromLine")
        self.completeToken = self.get_utils_func(".completeToken")
        self.retrieveCompletions = self.get_utils_func(".retrieveCompletions")
        self.initialized = True

    def get_completions(self, document, complete_event):
        if not self.initialized:
            self.initialize()
        token = ""
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
            if (len(token) >= 3 and text[-1].isalnum()) or complete_event.completion_requested:
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
                except Exception:
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
