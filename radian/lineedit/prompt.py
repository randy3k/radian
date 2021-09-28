from .buffer import ModalBuffer

from prompt_toolkit import PromptSession
from prompt_toolkit.application import Application
from prompt_toolkit.application.current import get_app
from prompt_toolkit.auto_suggest import DynamicAutoSuggest
from prompt_toolkit.completion import DynamicCompleter, ThreadedCompleter
from prompt_toolkit.enums import DEFAULT_BUFFER
from prompt_toolkit.filters import Condition
from prompt_toolkit.key_binding.key_bindings import DynamicKeyBindings, merge_key_bindings
from prompt_toolkit.validation import DynamicValidator
from prompt_toolkit.shortcuts.prompt import is_true, CompleteStyle
from prompt_toolkit.utils import to_str

from collections import OrderedDict
from typing import cast


class ModeSpec():
    def __init__(
            self,
            name,
            on_activated=None,
            on_dectivated=None,
            keep_history=True,
            history_share_with=False,
            switchable_to=True,
            switchable_from=True,
            prompt_key_bindings=None,
            **kwargs):

        def _ensure_func(x):
            if isinstance(x, bool):
                return lambda m: x
            elif isinstance(x, list):
                return lambda m: m in x
            elif isinstance(x, str):
                return lambda m: m == x
            else:
                return x

        self.name = name
        self.on_activated = on_activated
        self.on_dectivated = on_dectivated
        self.keep_history = keep_history
        self.history_share_with = _ensure_func(history_share_with)
        self.switchable_to = _ensure_func(switchable_to)
        self.switchable_from = _ensure_func(switchable_from)
        self.prompt_key_bindings = prompt_key_bindings
        for key in kwargs:
            if key not in PromptSession._fields:
                raise KeyError("unknown field", key)
            setattr(self, key, kwargs[key])


class ModalPromptSession(PromptSession):
    _current_mode = None
    _default_settings = {}
    _specs = OrderedDict()

    # new settings
    add_history = True
    search_no_duplicates = False

    def _check_args(self, kwargs):
        if "specs" in kwargs:
            specs = kwargs["specs"]
            for m in specs.values():
                assert isinstance(m, ModeSpec)

    def _filter_args(self, kwargs):
        for key in ["add_history", "search_no_duplicates"]:
            if key in kwargs:
                setattr(self, key, kwargs[key])
                del kwargs[key]

    def __init__(self, *args, **kwargs):
        self._check_args(kwargs)
        self._filter_args(kwargs)
        super().__init__(*args, **kwargs)
        self._backup_settings()

    # for backward compatibility
    @property
    def modes(self):
        return self._specs

    @property
    def specs(self):
        return self._specs

    @property
    def current_mode(self):
        return self._current_mode

    @property
    def current_mode_spec(self):
        return self.specs[self.current_mode]

    @property
    def main_mode(self):
        return next(iter(self.specs.keys())) if len(self.specs) > 0 else None

    @property
    def main_mode_spec(self):
        return self.specs[self.main_mode]

    def register_mode(self, spec):
        assert isinstance(spec, ModeSpec)

        self.specs[spec.name] = spec
        if len(self.specs) == 1:
            self.activate_mode(spec.name)
        else:
            self.activate_mode(self.current_mode, force=True)

    def unregister_mode(self, spec_or_name):
        if isinstance(spec_or_name, str):
            del self.specs[spec_or_name]
        else:
            del self.specs[next(iter(k for k, v in self.specs.items() if v == spec_or_name))]

    def change_mode(self, mode, force=False):
        if mode not in self.specs:
            raise Exception("no such mode")

        spec = self.specs[self.current_mode]
        newspec = self.specs[mode]

        if self.current_mode == mode and not force:
            return

        if spec.switchable_to(newspec.name) and newspec.switchable_from(spec.name):
            self.activate_mode(mode, force)

    def activate_mode(self, name, force=False):
        if name not in self.specs:
            raise Exception("no such mode")

        spec = self.specs[name]

        if self.current_mode == spec.name and not force:
            return

        if self.current_mode:
            current_spec = self.specs[self.current_mode]
            if current_spec.on_dectivated:
                current_spec.on_dectivated(self)

        self._current_mode = spec.name

        self._restore_settings()
        for name in self._fields:
            if name != "key_bindings":
                if hasattr(spec, name):
                    setattr(self, name, getattr(spec, name))

        self.key_bindings = merge_key_bindings(
            [
                DynamicKeyBindings(lambda: self.specs[self.current_mode].prompt_key_bindings)
            ] +
            [
                m.key_bindings for m in self.specs.values()
                if hasattr(m, "key_bindings") and m.key_bindings
            ]
        )

        if spec.on_activated:
            spec.on_activated(self)

    def _backup_settings(self):
        for name in self._fields:
            self._default_settings[name] = getattr(self, name)

    def _restore_settings(self):
        for name in self._fields:
            setattr(self, name, self._default_settings[name])

    def _create_default_buffer(self):
        """
        radian modifications
            supports both complete_while_typing and enable_history_search

        Create and return the default input buffer.
        """
        dyncond = self._dyncond

        # Create buffers list.
        def accept(buff) -> bool:
            # remember the last working index for history_forward
            buff.last_working_index = buff.working_index
            """Accept the content of the default buffer. This is called when
            the validation succeeds."""
            cast(Application[str], get_app()).exit(result=buff.document.text)
            return True  # Keep text, we call 'reset' later on.

        return ModalBuffer(
            name=DEFAULT_BUFFER,
            # Make sure that complete_while_typing is disabled when
            # enable_history_search is enabled. (First convert to Filter,
            # to avoid doing bitwise operations on bool objects.)
            complete_while_typing=Condition(
                lambda: is_true(self.complete_while_typing)
                # and not is_true(self.enable_history_search)
                and not self.complete_style == CompleteStyle.READLINE_LIKE
            ),
            validate_while_typing=dyncond("validate_while_typing"),
            enable_history_search=dyncond("enable_history_search"),
            validator=DynamicValidator(lambda: self.validator),
            completer=DynamicCompleter(
                lambda: ThreadedCompleter(self.completer)
                if self.complete_in_thread and self.completer
                else self.completer
            ),
            history=self.history,
            auto_suggest=DynamicAutoSuggest(lambda: self.auto_suggest),
            accept_handler=accept,
            tempfile_suffix=lambda: to_str(self.tempfile_suffix or ""),
            tempfile=lambda: to_str(self.tempfile or ""),
            session=self,
            search_no_duplicates=self.search_no_duplicates
        )

    def prompt(self, *args, **kwargs):
        self._check_args(kwargs)
        self._filter_args(kwargs)
        if args:
            raise Exception("positional arguments are deprecated")

        backup = self._default_settings.copy()
        for name in self._fields:
            if name in kwargs:
                value = kwargs[name]
                if value is not None:
                    setattr(self._default_settings, name, value)

        orig_mode = self.current_mode
        try:
            result = super().prompt(**kwargs)
        except KeyboardInterrupt:
            self._default_settings = backup.copy()
            self.activate_mode(orig_mode, force=True)
            raise KeyboardInterrupt
        finally:
            self._default_settings = backup.copy()

        # prompt will restore settings, we need to reactivate current mode
        self.activate_mode(self.current_mode, force=True)
        return result
