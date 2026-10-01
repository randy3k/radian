import asyncio
import os
import selectors
import threading
from asyncio import get_running_loop
from typing import cast

from prompt_toolkit import PromptSession
from prompt_toolkit.application import Application
from prompt_toolkit.application.current import get_app
from prompt_toolkit.auto_suggest import DynamicAutoSuggest
from prompt_toolkit.completion import DynamicCompleter, ThreadedCompleter
from prompt_toolkit.enums import DEFAULT_BUFFER
from prompt_toolkit.eventloop.inputhook import InputHookContext, InputHookSelector
from prompt_toolkit.filters import Condition, emacs_mode
from prompt_toolkit.key_binding.key_bindings import (
    DynamicKeyBindings,
    KeyBindings,
    merge_key_bindings,
)
from prompt_toolkit.shortcuts.prompt import CompleteStyle, is_true
from prompt_toolkit.utils import to_str
from prompt_toolkit.validation import DynamicValidator

from .buffer import ModalBuffer


# =============================================================================
# 1. InputHook Selector
# =============================================================================


class CustomInputHookSelector(InputHookSelector):
    def select(self, timeout=None):
        loop = get_running_loop()
        if len(getattr(loop, "_ready", [])) > 0:
            return self.selector.select(timeout=timeout)

        ready = False
        result = None
        exc = None

        def run_selector():
            nonlocal ready, result, exc
            try:
                result = self.selector.select(timeout=timeout)
            except BaseException as e:
                exc = e
            finally:
                try:
                    os.write(self._w, b"x")
                except OSError:
                    pass
                ready = True

        th = threading.Thread(target=run_selector)
        th.start()

        def input_is_ready():
            return ready

        try:
            self.inputhook(InputHookContext(self._r, input_is_ready))
        except BaseException:
            if not ready:
                try:
                    loop.call_soon_threadsafe(lambda: None)
                except RuntimeError:
                    pass
            raise
        finally:
            # Wait for the selector thread to finish before draining the pipe.
            # Avoids select.select([self._r], ...), which fails with
            # ValueError("filedescriptor out of range in select()") when
            # self._r >= FD_SETSIZE (1024); see #519 and
            # prompt-toolkit/python-prompt-toolkit#2111.
            th.join()
            try:
                os.read(self._r, 1024)
            except OSError:
                pass

        if exc is not None:
            raise exc
        assert result is not None
        return result

    def close(self):
        if self._r >= 0:
            os.close(self._r)
            os.close(self._w)

        self._r = self._w = -1
        self.selector.close()


# =============================================================================
# 2. Prompt Mode Definition
# =============================================================================


class PromptMode:
    def __init__(
        self,
        name,
        prompt_message=None,
        is_activated=None,
        callback=None,
        sticky=False,
        sticky_on_sigint=False,
        insert_new_line=False,
        insert_new_line_on_sigint=False,
        keep_history=True,
        history_book=None,
        key_bindings=None,
        prompt_key_bindings=None,
        **kwargs,
    ):
        self.name = name
        self.prompt_message = prompt_message
        self.is_activated = is_activated
        self.callback = callback
        self.sticky = sticky
        self.sticky_on_sigint = sticky_on_sigint
        self.insert_new_line = insert_new_line
        self.insert_new_line_on_sigint = insert_new_line_on_sigint
        self.keep_history = keep_history
        self.history_book = history_book or name
        self.key_bindings = key_bindings
        self.prompt_key_bindings = prompt_key_bindings
        for key in kwargs:
            if key not in PromptSession._fields:
                raise KeyError("unknown field", key)
        self.settings = kwargs


# =============================================================================
# 3. Modal Prompt Session
# =============================================================================


class ModalPromptSession(PromptSession):
    def __init__(
        self,
        *args,
        inputhook=None,
        add_history=True,
        search_no_duplicates=False,
        **kwargs,
    ):
        self._default_settings = {}
        self.modes = {}
        self.current_mode = None
        self._prompt_message = ""
        self._inputhook = inputhook
        self.add_history = add_history
        self.search_no_duplicates = search_no_duplicates
        super().__init__(*args, **kwargs)
        self._backup_settings()

    def mode_to_be_activated(self):
        for name in reversed(self.modes):
            mode = self.modes[name]
            if mode.is_activated and mode.is_activated(self):
                return name
        return "unknown"

    def register_mode(self, name, **kwargs):
        mode = PromptMode(name, **kwargs)
        self.modes[mode.name] = mode
        if len(self.modes) == 1:
            self.activate_mode(mode.name)
        else:
            self.activate_mode(self.current_mode.name, force=True)

    def activate_mode(self, name, force=False):
        if name not in self.modes:
            raise KeyError(f"unknown mode: {name}")

        mode = self.modes[name]
        if self.current_mode == mode and not force:
            return

        self.current_mode = mode
        self._restore_settings()
        for field, value in mode.settings.items():
            setattr(self, field, value)

        self.key_bindings = merge_key_bindings(
            [DynamicKeyBindings(lambda: self.current_mode.prompt_key_bindings)]
            + [m.key_bindings for m in self.modes.values() if m.key_bindings]
        )

    def _backup_settings(self):
        for name in self._fields:
            self._default_settings[name] = getattr(self, name)

    def _restore_settings(self):
        for name, value in self._default_settings.items():
            setattr(self, name, value)

    def _create_default_buffer(self):
        """
        radian modifications:
            supports both complete_while_typing and enable_history_search

        Create and return the default input buffer.
        """
        dyncond = self._dyncond

        def accept(buff) -> bool:
            cast(Application[str], get_app()).exit(result=buff.document.text)
            return True  # Keep text, we call 'reset' later on.

        return ModalBuffer(
            name=DEFAULT_BUFFER,
            complete_while_typing=Condition(
                lambda: is_true(self.complete_while_typing)
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
        )

    def _create_application(self, *args, **kwargs):
        app = super()._create_application(*args, **kwargs)

        kb = KeyBindings()

        # operate-and-get-next
        @kb.add("c-o", filter=emacs_mode)
        def _(event):
            buff = event.current_buffer
            if not isinstance(buff, ModalBuffer):
                return
            working_index = buff.working_index
            buff.validate_and_handle()

            def set_working_index() -> None:
                buff.go_to_next_history(working_index)

            event.app.pre_run_callables.append(set_working_index)

        app._default_bindings = merge_key_bindings([app._default_bindings, kb])

        orig_run = app.run

        def run(
            pre_run=None,
            set_exception_handler=True,
            handle_sigint=True,
            in_thread=False,
            inputhook=None,
        ):
            if inputhook is not None and not in_thread:
                coro = app.run_async(
                    pre_run=pre_run,
                    set_exception_handler=set_exception_handler,
                    handle_sigint=handle_sigint,
                )
                selector = CustomInputHookSelector(
                    selectors.DefaultSelector(), inputhook
                )
                loop = asyncio.SelectorEventLoop(selector)
                try:
                    return loop.run_until_complete(coro)
                finally:
                    try:
                        to_cancel = asyncio.all_tasks(loop)
                        if to_cancel:
                            for task in to_cancel:
                                task.cancel()
                            loop.run_until_complete(
                                asyncio.gather(*to_cancel, return_exceptions=True)
                            )
                        loop.run_until_complete(loop.shutdown_asyncgens())
                    finally:
                        loop.close()

            return orig_run(
                pre_run=pre_run,
                set_exception_handler=set_exception_handler,
                handle_sigint=handle_sigint,
                in_thread=in_thread,
                inputhook=inputhook,
            )

        app.run = run

        return app

    def prompt(
        self,
        *args,
        add_history=None,
        search_no_duplicates=None,
        **kwargs,
    ):
        if args:
            raise TypeError("positional arguments are not supported")
        if add_history is not None:
            self.add_history = add_history
        if search_no_duplicates is not None:
            self.search_no_duplicates = search_no_duplicates

        try:
            result = super().prompt(inputhook=self._inputhook, **kwargs)
        finally:
            self.activate_mode(self.current_mode.name, force=True)

        if self.current_mode.callback:
            result = self.current_mode.callback(self)

        return result
