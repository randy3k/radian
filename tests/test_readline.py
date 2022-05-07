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
