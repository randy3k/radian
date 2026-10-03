import sys
import pytest


def test_readline(terminal):
    # issue #106
    terminal.current_line().assert_startswith("r$>")
    terminal.write("cat('hello'); readline('> ')\n")
    terminal.previous_line(1).assert_startswith("hello")
    terminal.current_line().assert_startswith("> ")
    terminal.write("ok\n")
    terminal.previous_line(2).assert_contain("\"ok\"")

    # multiline backspace with fewer than tab_size leading spaces
    terminal.write("1 +\n  \x7f2\n")
    terminal.previous_line(2).assert_startswith("[1] 3")

    # builtin R completion
    terminal.write("R.version.str")
    terminal.current_line().assert_contains("R.version.str")
    terminal.write("\t")
    terminal.current_line().strip().assert_equal("r$> R.version.string")
    terminal.write("\n\n")
    terminal.previous_line(2).assert_contain("R version")


def test_askpass(terminal):
    # issue #359
    terminal.current_line().assert_startswith("r$>")
    terminal.write("askpass::askpass('askpass> ')\n")
    terminal.current_line().assert_startswith("askpass>")
    terminal.write("answer\n")
    terminal.previous_line(2).assert_contain("\"answer\"")


def test_renv(terminal, tmp_path):
    import os
    import time

    orig_wd = os.getcwd().replace("\\", "/")
    proj = tmp_path / "proj"
    proj.mkdir()
    renv_root = (tmp_path / "renv_root").as_posix()

    terminal.current_line().assert_startswith("r$>")
    terminal.write(
        f"Sys.setenv(RENV_PATHS_ROOT = '{renv_root}', RENV_WATCHDOG_ENABLED = 'FALSE'); "
        f"setwd('{proj.as_posix()}'); "
        "renv::init(bare = TRUE, restart = FALSE); "
        "cat('RENV_READY\\n')\n"
    )
    terminal.previous_line(2).assert_startswith("RENV_READY", timeout=30)
    terminal.current_line().strip().assert_equal("r$>")

    terminal.write("grepl('renv/library', normalizePath(.libPaths()[1], winslash = '/'))\n")
    terminal.previous_line(2).assert_startswith("[1] TRUE")
    terminal.current_line().strip().assert_equal("r$>")

    # In bare renv project, reticulate is not in .libPaths(), so '~' inserts literal '~'
    terminal.write("~")
    terminal.current_line().strip().assert_equal("r$> ~")
    terminal.sendintr()
    terminal.current_line().strip().assert_equal("r$>")

    # Hydrate askpass into renv/library and verify package completion updates immediately
    terminal.write("renv::hydrate('askpass', prompt = FALSE); cat('HYDRATED\\n')\n")
    terminal.previous_line(2).assert_startswith("HYDRATED", timeout=30)
    terminal.current_line().strip().assert_equal("r$>")

    terminal.write("askpa")
    terminal.current_line().assert_contains("askpa")
    terminal.write("\t")
    terminal.current_line().strip().assert_equal("r$> askpass::")
    terminal.sendintr()
    time.sleep(0.1)
    terminal.sendintr()
    terminal.current_line().strip().assert_equal("r$>")

    terminal.write("library(askpa")
    terminal.current_line().assert_contains("library(askpa")
    terminal.write("\t")
    terminal.current_line().strip().assert_startswith("r$> library(askpass")
    terminal.sendintr()
    time.sleep(0.1)
    terminal.sendintr()
    terminal.current_line().strip().assert_equal("r$>")

    terminal.write(f"renv::deactivate(); setwd('{orig_wd}'); cat('DEACTIVATED\\n')\n")
    terminal.previous_line(2).assert_startswith("DEACTIVATED", timeout=30)
    terminal.current_line().strip().assert_equal("r$>")


def test_strings(terminal):
    # issue #377, #523
    from prompt_toolkit.document import Document
    from radian.lexer import cursor_in_string


    assert not cursor_in_string(Document("", 0))
    assert cursor_in_string(Document('"', 1))
    assert cursor_in_string(Document('"hello', 6))
    assert cursor_in_string(Document('"hello (', 8))
    assert cursor_in_string(Document('"hello\\nworld', 12))
    assert cursor_in_string(Document('"hello \\"world', 14))
    assert not cursor_in_string(Document('"hello"', 7))
    assert not cursor_in_string(Document('"hello" ', 8))
    assert cursor_in_string(Document('r"(', 3))
    assert cursor_in_string(Document('r"(hello', 8))
    assert not cursor_in_string(Document('r"(hello)"', 10))
    assert cursor_in_string(Document('r"--(hello )-"', 14))
    assert not cursor_in_string(Document('r"--(hello )--"', 15))

    terminal.current_line().assert_startswith("r$>")
    terminal.write("x <- 'a'\n")
    terminal.current_line().strip().assert_equal("r$>")
    terminal.write("nchar(x)\n")
    terminal.previous_line(2).assert_startswith("[1] 1")

    terminal.write('y <- c("a\\"b", r"(hello (world) "test")")\n')
    terminal.current_line().strip().assert_equal("r$>")
    terminal.write("nchar(y)\n")
    terminal.previous_line(2).assert_startswith("[1]  3 20")


@pytest.mark.skipif(sys.platform.startswith("win"), reason="windows doesn't support bpm.")
def test_strings_bracketed(terminal):
    terminal.current_line().assert_startswith("r$>")
    terminal.write("\x1b[200~x <- '" + 'a'*10 + "'\x1b[201~\n")
    terminal.current_line().strip().assert_equal("r$>")
    terminal.write("nchar(x)\n")
    terminal.previous_line(2).assert_startswith("[1] 10")

    terminal.write("\x1b[200~x <- '" + 'a'*5000 + "'\x1b[201~\n")
    terminal.current_line().strip().assert_equal("r$>")
    terminal.write("nchar(x)\n")
    terminal.previous_line(2).assert_startswith("[1] 5000")

    terminal.write("\x1b[200~x <- '" + 'a'*2000 + '\n' + 'b'*2000 + "'\x1b[201~\n")
    terminal.current_line().strip().assert_equal("r$>")
    terminal.write("nchar(x)\n")
    terminal.previous_line(2).assert_startswith("[1] 4001")

    s = '中'*1000 + '\n' + '文'*1000 + '\n' + '中'*1000 + '\n' + '文'*1000

    terminal.write("\x1b[200~x <- '" + s + "'\x1b[201~\n")
    terminal.current_line().strip().assert_equal("r$>")
    terminal.write("nchar(x)\n")
    terminal.previous_line(2).assert_startswith("[1] 4003")

    # different padding
    terminal.write("\x1b[200~xy <- '" + s + "'\x1b[201~\n")
    terminal.current_line().strip().assert_equal("r$>")
    terminal.write("nchar(xy)\n")
    terminal.previous_line(2).assert_startswith("[1] 4003")


def test_early_termination(terminal):
    terminal.current_line().assert_startswith("r$>")
    terminal.write("Sys.setlocale(category = 'LC_MESSAGES', locale = 'en_US.UTF8'); stop('!')\x1b\rd = 1\n")
    terminal.previous_line(2).assert_startswith("Error")
    terminal.write("d\n")
    terminal.previous_line(2).assert_startswith("Error: object 'd' not found")


def test_utf8(terminal):
    terminal.current_line().assert_startswith("r$>")
    terminal.write("l10n_info()[['UTF-8']]\n")
    terminal.previous_line(2).assert_startswith("[1] TRUE")
    if sys.platform.startswith("win"):
        terminal.write("l10n_info()[['system.codepage']]\n")
        terminal.previous_line(2).assert_startswith("[1] 65001")
    terminal.write("x <- 'ěščřžýáíé 中文'\n")
    terminal.current_line().strip().assert_equal("r$>")
    terminal.write("cat(Encoding(x), nchar(x), '\\n')\n")
    terminal.previous_line(2).assert_startswith("UTF-8 12")


def test_history(tmp_path):
    from radian.lineedit.history import ModalFileHistory

    hist_file = str(tmp_path / "radian_history")
    h1 = ModalFileHistory(hist_file, max_history_size=10)
    list(h1.load())
    for i in range(12):
        h1.append_string(f"line_{i}\ncont_{i}", "r" if i % 2 == 0 else "shell")

    # Reload with max_history_size=10; 12 > 10 so it should trim to round(10 * 0.9) = 9 entries
    h2 = ModalFileHistory(hist_file, max_history_size=10)
    list(h2.load())
    assert h2.get_strings() == [f"line_{i}\ncont_{i}" for i in range(3, 12)]
    assert h2.get_modes() == ["r" if i % 2 == 0 else "shell" for i in range(3, 12)]

    # Reload again from the trimmed file on disk to verify on-disk integrity
    h3 = ModalFileHistory(hist_file, max_history_size=10)
    list(h3.load())
    assert h3.get_strings() == [f"line_{i}\ncont_{i}" for i in range(3, 12)]
    assert h3.get_modes() == ["r" if i % 2 == 0 else "shell" for i in range(3, 12)]


def test_history_search(terminal):
    terminal.current_line().assert_startswith("r$>")
    terminal.write("apple_val <- 111\n")
    terminal.previous_line(2).assert_contain("apple_val <- 111")
    terminal.current_line().strip().assert_equal("r$>")
    terminal.write("apple_val <- 222\n")
    terminal.previous_line(2).assert_contain("apple_val <- 222")
    terminal.current_line().strip().assert_equal("r$>")
    # Enter shell mode, run a command containing 'apple_val', then return to R mode
    terminal.write(";echo apple_val_shell\n")
    terminal.previous_line(2).assert_startswith("apple_val_shell")
    terminal.current_line().strip().assert_equal("#!>")
    # In shell mode, Ctrl-R should find the shell command, not the R ones;
    # Ctrl-G (\x07) aborts search and restores the empty shell prompt
    terminal.write("echo other_shell\n")
    terminal.previous_line(2).assert_startswith("other_shell")
    terminal.current_line().strip().assert_equal("#!>")
    terminal.write("\x12apple_val")
    terminal.current_line().assert_contain("echo apple_val_shell")
    terminal.write("\x07")
    terminal.current_line().strip().assert_equal("#!>")
    terminal.write("\x7f")
    terminal.current_line().strip().assert_equal("r$>")

    # Ctrl-R search for 'apple_val' in R mode should skip shell history and find 'apple_val <- 222'
    terminal.write("\x12apple_val")
    terminal.current_line().assert_contain("apple_val <- 222")
    # Pressing Ctrl-R again finds the older 'apple_val <- 111'
    terminal.write("\x12")
    terminal.current_line().assert_contain("apple_val <- 111")
    # Pressing Ctrl-S (\x13) reverses direction back to 'apple_val <- 222', then Ctrl-R back to '111'
    terminal.write("\x13")
    terminal.current_line().assert_contain("apple_val <- 222")
    terminal.write("\x12\r\r")
    terminal.current_line().strip().assert_equal("r$>")
    terminal.write("apple_val\n")
    terminal.previous_line(2).assert_startswith("[1] 111")

    # Prefix history search with Up (\x1b[A) and Down (\x1b[B) arrows skips shell mode
    terminal.write("apple_val <- \x1b[A")
    terminal.current_line().assert_contain("apple_val <- 111")
    terminal.write("\x1b[A")
    terminal.current_line().assert_contain("apple_val <- 222")
    terminal.write("\x1b[B")
    terminal.current_line().assert_contain("apple_val <- 111")
    terminal.sendintr()
    terminal.current_line().strip().assert_equal("r$>")

    # Browse mode shares 'r' history_book and ignores browser commands ('n', 'Q', etc.) in history
    terminal.write("browser()\n")
    terminal.current_line().strip().assert_equal("Browse[1]>")
    terminal.write("browse_apple <- 333\n")
    terminal.previous_line(2).assert_contain("browse_apple <- 333")
    terminal.current_line().strip().assert_equal("Browse[1]>")
    terminal.write("Q\n")
    terminal.current_line().strip().assert_equal("r$>")
    # 'Q' was ignored, so Up arrow recalls 'browse_apple <- 333' directly
    terminal.write("\x1b[A")
    terminal.current_line().assert_contain("browse_apple <- 333")
    terminal.sendintr()
    terminal.current_line().strip().assert_equal("r$>")


def test_history_search_options(radian_command, tmp_path):
    import time
    from .terminal import Terminal

    profile = tmp_path / "radian_profile"
    profile.write_text(
        "options(radian.history_search_no_duplicates = TRUE)\n"
        "options(radian.history_search_ignore_case = TRUE)\n"
        "options(radian.escape_key_map = list(list(key = '-', value = ' <- ')))\n"
    )

    cmd = radian_command + ["--no-history", f"--profile={profile}"]
    with Terminal.open(cmd) as terminal:
        try:
            terminal.current_line().assert_startswith("r$>")
            # Test escape_key_map (which binds via session.modes['r'].prompt_key_bindings)
            terminal.write("dup_item\x1b-20\n")
            terminal.previous_line(2).assert_contain("dup_item <- 20")
            terminal.current_line().strip().assert_equal("r$>")
            # Layout of history:
            # 0: dup_item <- 20 (older duplicate before oldest unique match!)
            # 1: dup_item <- 10 (oldest unique match)
            # 2: dup_item <- 20
            # 3: other_cmd <- 99
            # 4: dup_item <- 20 (newest duplicate)
            terminal.write("dup_item <- 10\n")
            terminal.previous_line(2).assert_contain("dup_item <- 10")
            terminal.current_line().strip().assert_equal("r$>")
            terminal.write("dup_item <- 20\n")
            terminal.previous_line(2).assert_contain("dup_item <- 20")
            terminal.current_line().strip().assert_equal("r$>")
            terminal.write("other_cmd <- 99\n")
            terminal.previous_line(2).assert_contain("other_cmd <- 99")
            terminal.current_line().strip().assert_equal("r$>")
            terminal.write("dup_item <- 20\n")
            terminal.previous_line(2).assert_contain("dup_item <- 20")
            terminal.current_line().strip().assert_equal("r$>")

            # Case-insensitive Ctrl-R search for 'DUP_ITEM':
            # 1st match is 'dup_item <- 20' (index 4)
            terminal.write("\x12DUP_ITEM")
            terminal.current_line().assert_contain("dup_item <- 20")
            # Pressing Ctrl-R once should skip index 2 ('dup_item <- 20') and find 'dup_item <- 10' (index 1)
            terminal.write("\x12")
            terminal.current_line().assert_contain("dup_item <- 10")
            # Pressing Ctrl-R again at the oldest unique match should NOT match index 0 ('dup_item <- 20'),
            # and accepting + executing should run 'dup_item <- 10'
            terminal.write("\x12\r\r")
            terminal.current_line().strip().assert_equal("r$>")
            terminal.write("dup_item\n")
            terminal.previous_line(2).assert_startswith("[1] 10")

            # Multiple occurrences on the same line + Ctrl-S forward search with search_no_duplicates:
            # 'dup_item ' (with trailing space) occurs twice on 'dup_item <- dup_item + 5'
            terminal.write("dup_item <- dup_item + 5\n")
            terminal.previous_line(2).assert_contain("dup_item <- dup_item + 5")
            terminal.current_line().strip().assert_equal("r$>")
            # 1st match is 2nd 'dup_item ' on 'dup_item <- dup_item + 5'
            terminal.write("\x12dup_item ")
            terminal.current_line().assert_contain("dup_item <- dup_item + 5")
            # Next Ctrl-R moves to 1st 'dup_item ' on the same line
            terminal.write("\x12")
            terminal.current_line().assert_contain("dup_item <- dup_item + 5")
            # Next Ctrl-R moves to 'dup_item <- 10', then skips duplicate '10' to 'dup_item <- 20'
            terminal.write("\x12")
            terminal.current_line().assert_contain("dup_item <- 10")
            terminal.write("\x12")
            terminal.current_line().assert_contain("dup_item <- 20")
            # Ctrl-S (\x13) reverses direction to forward search ('dup_item <- 10'),
            # then next Ctrl-S steps forward to 'dup_item <- dup_item + 5'
            terminal.write("\x13")
            terminal.current_line().assert_contain("dup_item <- 10")
            terminal.write("\x13\r\r")
            terminal.current_line().strip().assert_equal("r$>")
            terminal.write("dup_item\n")
            terminal.previous_line(2).assert_startswith("[1] 20")
        finally:
            terminal.sendintr()
            terminal.write("q()\n")
            start_time = time.time()
            while terminal.isalive():
                if time.time() - start_time > 15:
                    raise Exception("radian didn't quit cleanly")
                time.sleep(0.1)


def test_modal_prompt_session():
    from prompt_toolkit.input import create_pipe_input
    from prompt_toolkit.output import DummyOutput
    from radian.lineedit.history import ModalInMemoryHistory
    from radian.lineedit.prompt import ModalPromptSession, PromptMode

    with pytest.raises(KeyError):
        PromptMode("bad", nonexistent_field=True)

    with create_pipe_input() as pipe_input:
        session = ModalPromptSession(
            history=ModalInMemoryHistory(),
            input=pipe_input,
            output=DummyOutput(),
            multiline=False,
            add_history=True,
            search_no_duplicates=True,
        )
        assert session.add_history is True
        assert session.search_no_duplicates is True

        session.register_mode(
            "r",
            is_activated=lambda s: s._prompt_message == "r$> ",
            history_book="r",
            multiline=True,
        )
        session.register_mode(
            "shell",
            is_activated=lambda s: s._prompt_message == "#!> ",
            history_book="shell",
            multiline=False,
        )

        # First registered mode is automatically activated
        assert isinstance(session.current_mode, PromptMode)
        assert session.current_mode.name == "r"
        assert session.current_mode is session.modes["r"]
        assert session.multiline is True

        # Switching modes restores default settings and applies the target mode's settings
        session.activate_mode("shell")
        assert session.current_mode is session.modes["shell"]
        assert session.current_mode.name == "shell"
        assert session.multiline is False

        with pytest.raises(KeyError):
            session.activate_mode("nonexistent")

        # mode_to_be_activated checks registered modes in reverse order
        session._prompt_message = "r$> "
        assert session.mode_to_be_activated() == "r"
        session._prompt_message = "other> "
        assert session.mode_to_be_activated() == "unknown"


def test_inputhook_select_and_cleanup(monkeypatch):
    # issue #519
    import gc
    import os
    import selectors
    import time
    import prompt_toolkit.eventloop.inputhook as pt_ih
    from prompt_toolkit.input import create_pipe_input
    from prompt_toolkit.output import DummyOutput
    from radian.lineedit.history import ModalInMemoryHistory
    from radian.lineedit.prompt import CustomInputHookSelector, ModalPromptSession

    hook_fds = []
    hook_action = [None]

    def dummy_inputhook(context):
        hook_fds.append(context.fileno())
        if hook_action[0] is not None:
            action, hook_action[0] = hook_action[0], None
            action()
        while not context.input_is_ready():
            time.sleep(0.005)

    with create_pipe_input() as pipe_input:
        session = ModalPromptSession(
            history=ModalInMemoryHistory(),
            input=pipe_input,
            output=DummyOutput(),
            multiline=False,
            inputhook=dummy_inputhook,
        )
        session.register_mode(
            "r",
            is_activated=lambda s: True,
            history_book="r",
            multiline=False,
        )

        # 1. Verify KeyboardInterrupt (both from key press and raised inside inputhook)
        # closes the inputhook event loop and pipe FDs immediately without GC
        gc.collect()
        gc.disable()
        try:
            for _ in range(3):
                hook_fds.clear()
                hook_action[0] = lambda: pipe_input.send_text("\x03")
                with pytest.raises(KeyboardInterrupt):
                    session.prompt()
                assert hook_fds
                for fd in set(hook_fds):
                    with pytest.raises(OSError):
                        os.fstat(fd)

            hook_fds.clear()

            def raise_interrupt():
                raise KeyboardInterrupt

            hook_action[0] = raise_interrupt
            with pytest.raises(KeyboardInterrupt):
                session.prompt()
            assert hook_fds
            for fd in set(hook_fds):
                with pytest.raises(OSError):
                    os.fstat(fd)
        finally:
            gc.enable()

        # 2. Verify high file descriptor (>= 1024) in inputhook pipe does not fail select()
        if not sys.platform.startswith("win"):
            import fcntl
            import resource

            soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
            min_fd = 1024
            if hard == resource.RLIM_INFINITY or hard > min_fd:
                try:
                    if soft <= min_fd:
                        new_soft = (
                            min_fd + 64
                            if hard == resource.RLIM_INFINITY
                            else min(hard, min_fd + 64)
                        )
                        resource.setrlimit(resource.RLIMIT_NOFILE, (new_soft, hard))

                    orig_pipe = os.pipe

                    def high_pipe():
                        r, w = orig_pipe()
                        high_r = fcntl.fcntl(r, fcntl.F_DUPFD_CLOEXEC, min_fd)
                        os.close(r)
                        return high_r, w

                    with monkeypatch.context() as m:
                        m.setattr(pt_ih.os, "pipe", high_pipe)
                        hook_fds.clear()
                        hook_action[0] = lambda: pipe_input.send_text("1 + 1\n")
                        result = session.prompt()
                        assert result == "1 + 1"
                        assert hook_fds and all(fd >= min_fd for fd in hook_fds)
                        for fd in set(hook_fds):
                            with pytest.raises(OSError):
                                os.fstat(fd)
                finally:
                    if soft <= min_fd:
                        resource.setrlimit(resource.RLIMIT_NOFILE, (soft, hard))

        # 3. Verify CustomInputHookSelector.close() is idempotent
        sel = CustomInputHookSelector(selectors.DefaultSelector(), dummy_inputhook)
        r_fd, w_fd = sel._r, sel._w
        sel.close()
        assert sel._r == -1 and sel._w == -1
        sel.close()  # second close should be a no-op
        with pytest.raises(OSError):
            os.fstat(r_fd)
        with pytest.raises(OSError):
            os.fstat(w_fd)


def test_completion_unit(monkeypatch, tmp_path):
    from prompt_toolkit.completion import CompleteEvent
    from prompt_toolkit.document import Document
    from radian.completion import RCompleter, SmartPathCompleter
    from radian.lexer import cursor_in_comment, cursor_in_string

    # 1. cursor_in_comment and cursor_in_string checks (including raw strings & unclosed backticks)
    assert not cursor_in_comment(Document("x <- 1", 6))
    assert not cursor_in_comment(Document('x <- "# not comment"', 20))
    assert cursor_in_comment(Document("# comment", 9))
    assert cursor_in_comment(Document("x <- 1 # comment", 16))
    assert not cursor_in_comment(Document("# comment\nx <- 1", 16))
    assert not cursor_in_comment(Document("df$`col#1", 9))
    assert not cursor_in_string(Document('df$`col"1', 9))
    assert not cursor_in_string(Document('x <- "a"; df$`col', 17))
    assert cursor_in_string(Document('r"(', 3))
    assert cursor_in_string(Document('r"(hello', 8))
    assert not cursor_in_string(Document('r"(hello)"', 10))
    assert not cursor_in_string(Document('r"()"', 5))
    assert cursor_in_string(Document('r"-----(hello )----"', 20))
    assert not cursor_in_string(Document('r"-----(hello )-----"', 21))

    # 2. RCompleter prefix & comment checks
    calls = []

    def fake_complete_line(buf, timeout=0, in_print=False):
        calls.append((buf, timeout, in_print))
        if buf.endswith("is."):
            return "is.", ["is.null", "is.na"]
        if buf.endswith("is.n"):
            return "is.n", ["is.null", "is.na"]
        if buf.endswith("R.version.s"):
            return "R.version.s", ["R.version.string"]
        if buf.endswith("utils::"):
            return "utils::", ["utils::str", "utils::sessionInfo"]
        if buf.endswith("utils::s"):
            return "utils::s", ["utils::str", "utils::sessionInfo"]
        if buf.endswith("mtcars$"):
            return "mtcars$", ["mtcars$mpg", "mtcars$cyl"]
        if buf.endswith("mtcars$m"):
            return "mtcars$m", ["mtcars$mpg"]
        if buf.endswith("s4obj@s"):
            return "s4obj@s", ["s4obj@slot1"]
        return "", ["from=", "to="]

    monkeypatch.setattr("radian.completion._complete_line", fake_complete_line)
    monkeypatch.setattr(
        "radian.completion.installed_packages", lambda: ["utils", "utf8", "stats"]
    )

    completer = RCompleter()
    typing_event = CompleteEvent(completion_requested=False)
    tab_event = CompleteEvent(completion_requested=True)

    # Punctuation, operators, numbers, and single-colon sequences do NOT auto-complete while typing
    for text in [
        "seq(c()",
        "seq((",
        'seq("a",',
        "seq(x <-",
        "x <-",
        "x ==",
        "df |>",
        "1:5",
        "x:",
        "123",
        "3.14",
        ".5",
        "::",
        "$$",
        "# utils",
    ]:
        calls.clear()
        comps = [c.text for c in completer.get_completions(Document(text, len(text)), typing_event)]
        assert comps == [], f"unexpected completions for {text!r}: {comps}"
        assert calls == []

    # Comments do not complete even on <Tab>
    assert list(completer.get_completions(Document("# utils", 7), tab_event)) == []

    # Dotted identifiers, namespace operators, and $/@@ chains DO auto-complete while typing
    for text, expected in [
        ("is.", ["is.null", "is.na"]),
        ("is.n", ["is.null", "is.na"]),
        ("R.version.s", ["R.version.string"]),
        ("utils::", ["utils::str", "utils::sessionInfo"]),
        ("utils::s", ["utils::str", "utils::sessionInfo"]),
        ("mtcars$", ["mtcars$mpg", "mtcars$cyl"]),
        ("mtcars$m", ["mtcars$mpg"]),
        ("s4obj@s", ["s4obj@slot1"]),
    ]:
        comps = [c.text for c in completer.get_completions(Document(text, len(text)), typing_event)]
        assert comps == expected, f"failed for {text!r}: {comps}"

    # Package completions inside library(): exact match is filtered out once fully typed,
    # and <Tab> right after library( / library(" / require( / requireNamespace(" lists all packages
    assert [
        c.text
        for c in completer.get_completions(Document("library(", 8), typing_event)
    ] == []
    assert [
        c.text
        for c in completer.get_completions(Document("library(", 8), tab_event)
    ] == ["utils", "utf8", "stats"]
    assert [
        c.text
        for c in completer.get_completions(Document('library("', 9), tab_event)
    ] == ["utils", "utf8", "stats"]
    assert [
        c.text
        for c in completer.get_completions(Document("require(", 8), tab_event)
    ] == ["utils", "utf8", "stats"]
    assert [
        c.text
        for c in completer.get_completions(Document('requireNamespace("', 18), tab_event)
    ] == ["utils", "utf8", "stats"]
    assert [
        c.text
        for c in completer.get_completions(Document("library(ut", 10), typing_event)
    ] == ["utils", "utf8"]
    assert [
        c.text
        for c in completer.get_completions(Document("library(utils", 13), typing_event)
    ] == []

    # LaTeX completions respect completion_prefix_length while typing, including \^2 and \_2
    assert list(completer.get_completions(Document(r"\a", 2), typing_event)) == []
    assert list(completer.get_completions(Document(r'"hello\n', 8), typing_event)) == []
    assert any(
        c.text == "α"
        for c in completer.get_completions(Document(r"\al", 3), typing_event)
    )
    assert any(
        c.text == "²"
        for c in completer.get_completions(Document(r"\^2", 3), typing_event)
    )
    assert any(
        c.text == "α"
        for c in completer.get_completions(Document(r"\alpha", 6), typing_event)
    )

    # 3. SmartPathCompleter trailing space and ~ handling
    sub = tmp_path / "subdir"
    sub.mkdir()
    (tmp_path / "file_a.txt").write_text("a")
    monkeypatch.chdir(tmp_path)

    path_completer = SmartPathCompleter()
    # Trailing space after non-cd command completes in cwd with start_position == 0
    ls_comps = list(path_completer.get_completions(Document("ls ", 3), tab_event))
    assert any(c.text == "file_a.txt" and c.start_position == 0 for c in ls_comps)
    ls_arg_comps = list(
        path_completer.get_completions(Document("ls file_a.txt ", 14), tab_event)
    )
    assert any(c.text == "subdir" and c.start_position == 0 for c in ls_arg_comps)

    # Bare "cd ~" does not replace "~" with the username
    assert list(path_completer.get_completions(Document("cd ~", 4), tab_event)) == []


def test_read_console_clears_stale_multiline_buffer():
    from types import SimpleNamespace
    from radian.console import create_read_console
    from radian.settings import radian_settings as settings

    long_multiline = "x <- '" + ("文字" * 600) + "'\ny <- 42"
    prompts = [long_multiline, "z <- 99"]

    def fake_prompt(add_history=1):
        return prompts.pop(0)

    session = SimpleNamespace(
        app=SimpleNamespace(
            is_running=False,
            output=SimpleNamespace(write_raw=lambda s: None),
        ),
        current_mode=SimpleNamespace(
            name="r",
            sticky=True,
            sticky_on_sigint=True,
            insert_new_line=False,
            insert_new_line_on_sigint=False,
        ),
        mode_to_be_activated=lambda: "r",
        activate_mode=lambda m: None,
        prompt=fake_prompt,
        _prompt_message=settings.prompt,
    )

    rc = create_read_console(session)
    # First top-level read starts line-by-line delivery ("{")
    assert rc(settings.prompt, 1) == "{"
    # Continuation prompt "+ " receives line 1
    assert rc("+ ", 1).startswith("x <- '")
    # If R aborts due to syntax error and returns to top-level prompt (settings.prompt),
    # stale remaining lines ("y <- 42", "}") are discarded and a fresh prompt is read!
    assert rc(settings.prompt, 1) == "z <- 99"
