from __future__ import unicode_literals


def test_startup(terminal):
    terminal.line(0).assert_startswith("R ")
    terminal.cursor().assert_equal((4, 3))
    terminal.current_line().assert_startswith("r$>")
    terminal.write("\n")
    terminal.current_line().assert_startswith("r$>")
    terminal.cursor().assert_equal((4, 5))
    terminal.sendintr()
    terminal.current_line().assert_startswith("r$>")
    terminal.cursor().assert_equal((4, 7))
