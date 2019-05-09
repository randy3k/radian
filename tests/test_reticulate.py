from __future__ import unicode_literals


def test_reticulate(terminal):
    terminal.current_line().assert_startswith("r$>")
    terminal.write("~")
    terminal.previous_line(3).assert_startswith("Python")
    terminal.previous_line(2).assert_startswith("Reticulate")
    terminal.current_line().assert_startswith(">>> ")
    terminal.write("imp")
    terminal.current_line().assert_contains("imp")
    terminal.write("\t")
    terminal.current_line().assert_contains("import")
    terminal.write(" os\n")
    terminal.current_line().strip().assert_equal(">>>")
    terminal.write("\b")
    terminal.previous_line(2).strip().assert_equal(">>> exit")
    terminal.current_line().strip().assert_startswith("r$>")
    terminal.write("~")
    terminal.current_line().strip().assert_equal(">>>")
    terminal.write("\x04")
    terminal.previous_line(2).strip().assert_equal(">>> exit")
    terminal.current_line().strip().assert_startswith("r$>")
