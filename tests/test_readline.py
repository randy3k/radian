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
