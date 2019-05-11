from __future__ import unicode_literals


def test_reticulate(terminal):
    terminal.current_line().assert_startswith("r$>")
    terminal.write("~")
    terminal.previous_line(3).assert_startswith("Python", timeout=60)
    terminal.previous_line(2).assert_startswith("Reticulate")
    terminal.current_line().strip().assert_equal(">>>")
    terminal.write("a = 1\n")
    terminal.current_line().strip().assert_equal(">>>")
    terminal.write("a\n")
    terminal.previous_line(2).strip().assert_equal("1")
    terminal.write("def f():\n")
    # auto indented
    terminal.current_line().assert_startswith(" ")
    terminal.write("pass\n")
    terminal.current_line().strip().assert_equal(">>>")


def test_multiline(terminal):
    terminal.current_line().assert_startswith("r$>")
    terminal.write("~")
    terminal.current_line().strip().assert_equal(">>>")
    # we need to add a delay between '\x1b' and '\r' in Windows
    terminal.write("b = 2\x1b")
    terminal.current_line().assert_startswith(">>> b = 2")
    terminal.write("\rc = 3")
    terminal.previous_line(1).strip().assert_equal(">>> b = 2")
    terminal.current_line().strip().assert_equal("c = 3")
    terminal.write("\n")
    terminal.current_line().strip().assert_equal(">>>")
    terminal.write("c\n")
    terminal.previous_line(2).strip().assert_equal("3")


def test_exit(terminal):
    terminal.current_line().assert_startswith("r$>")
    terminal.write("~")
    terminal.current_line().strip().assert_equal(">>>")
    terminal.write("\b")
    terminal.previous_line(2).strip().assert_equal(">>> exit")
    terminal.current_line().strip().assert_startswith("r$>")
    terminal.write("~")
    terminal.current_line().strip().assert_equal(">>>")
    terminal.write("\x04")
    terminal.previous_line(2).strip().assert_equal(">>> exit")
    terminal.current_line().strip().assert_startswith("r$>")


def test_completion(terminal):
    terminal.current_line().assert_startswith("r$>")
    terminal.write("~")
    terminal.current_line().strip().assert_equal(">>>")
    terminal.write("imp")
    terminal.current_line().assert_contains("imp")
    terminal.write("\t")
    terminal.current_line().assert_contains("import")
    terminal.write(" os\n")
