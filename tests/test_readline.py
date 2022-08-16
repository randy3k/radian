import time


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
    # issue #377
    terminal.current_line().assert_startswith("r$>")
    terminal.write("x <- 'a'\n")
    terminal.current_line().strip().assert_equal("r$>")
    terminal.write("nchar(x)\n")
    terminal.previous_line(2).assert_startswith("[1] 1")

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

    terminal.write("\x1b[200~x <- '" + '中'*1000 + '\n' + '文'*1000 + "'\x1b[201~\n")
    terminal.current_line().strip().assert_equal("r$>")
    terminal.write("nchar(x)\n")
    terminal.previous_line(2).assert_startswith("[1] 2001")
