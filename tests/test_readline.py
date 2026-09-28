import sys
import pytest


def test_readline(terminal):
    # issue #106
    terminal.current_line().assert_startswith("r$>")
    terminal.write("cat('hello'); readline('> ')\n")
    terminal.previous_line(1).assert_startswith("hello")
    terminal.current_line().assert_startswith("> ")


def test_askpass(terminal):
    # issue #359
    terminal.current_line().assert_startswith("r$>")
    terminal.write("askpass::askpass('askpass> ')\n")
    terminal.current_line().assert_startswith("askpass>")
    terminal.write("answer\n")
    terminal.previous_line(2).assert_contain("\"answer\"")


def test_strings(terminal):
    # issue #377, #523
    from prompt_toolkit.document import Document
    from radian.document import cursor_in_string

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

