import time


def exit_reticulate_prompt(t):
    t.sendintr()
    t.write("exit\n")


def test_reticulate(terminal):
    terminal.current_line().assert_startswith("r$>")
    terminal.write("~")
    terminal.previous_line(4).assert_startswith("Python", timeout=60)
    terminal.previous_line(3).assert_startswith("Reticulate")
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
    exit_reticulate_prompt(terminal)


def test_multiline(terminal):
    terminal.current_line().assert_startswith("r$>")
    terminal.write("~")
    terminal.current_line().strip().assert_equal(">>>")
    terminal.write("b = 2")
    terminal.current_line().assert_startswith(">>> b = 2")
    terminal.write("\x1b")
    # we need to add a delay between '\x1b' and '\r' in Windows
    time.sleep(0.1)
    terminal.write("\rc = 3")
    terminal.previous_line(1).strip().assert_equal(">>> b = 2")
    terminal.current_line().strip().assert_equal("c = 3")
    terminal.write("\n")
    terminal.current_line().strip().assert_equal(">>>")
    terminal.write("c\n")
    terminal.previous_line(2).strip().assert_equal("3")
    exit_reticulate_prompt(terminal)


def test_ctrl_d(terminal):
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
    exit_reticulate_prompt(terminal)
