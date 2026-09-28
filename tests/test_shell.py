import os


def test_shell(terminal):
    terminal.current_line().assert_startswith("r$>")
    terminal.write(";")
    terminal.current_line().assert_startswith("#!>")
    terminal.write("git --version\n")
    terminal.previous_line(2).assert_startswith("git version")
    terminal.current_line().assert_startswith("#!>")
    terminal.write("\b")
    terminal.current_line().assert_startswith("r$>")


def test_cd(terminal):
    terminal.current_line().assert_startswith("r$>")
    terminal.write(";")
    d = os.path.realpath(os.path.join(os.path.dirname(__file__), "..", "radi"))
    terminal.write("cd {}".format(d))
    terminal.current_line().strip().assert_endswith(os.sep + "radi")
    try:
        terminal.write("\t")
        terminal.current_line().strip().assert_endswith(os.sep + "radian")
    except Exception:
        terminal.write("\t")
        terminal.current_line().strip().assert_endswith(os.sep + "radian")
    terminal.write("\n")
    terminal.previous_line(2).strip().assert_endswith(os.sep + "radian")
    terminal.write("cd -\n")
    terminal.previous_line(2).strip().assert_equal(os.getcwd())
    terminal.current_line().assert_startswith("#!>")


def test_cd2(terminal):
    terminal.current_line().assert_startswith("r$>")
    terminal.write(";")
    d = os.path.realpath(os.path.join(os.path.dirname(__file__), "..", "radi"))
    terminal.write("cd \"{}".format(d))
    terminal.current_line().strip().assert_endswith(os.sep + "radi")
    try:
        terminal.write("\t")
        terminal.current_line().strip().assert_endswith(os.sep + "radian")
    except Exception:
        terminal.write("\t")
        terminal.current_line().strip().assert_endswith(os.sep + "radian")
    terminal.write("\"\n")
    terminal.previous_line(2).strip().assert_endswith(os.sep + "radian")
    terminal.write("cd -\n")
    terminal.previous_line(2).strip().assert_equal(os.getcwd())
    terminal.current_line().assert_startswith("#!>")

    # bare cd to home and cd - back
    import sys
    from prompt_toolkit.document import Document
    from prompt_toolkit.completion import CompleteEvent
    from radian.shell import run_command
    import radian.completion as completion_mod
    from radian.completion import RCompleter, SmartPathCompleter

    if not sys.platform.startswith("win"):
        run_command("# comment only")
    run_command("   ")

    orig_installed = completion_mod.installed_packages
    completion_mod.installed_packages = lambda: ["stats", "utils"]
    try:
        rc = RCompleter()
        ev = CompleteEvent(completion_requested=True)
        assert [c.text for c in rc.get_package_completions(Document("utils::st", 9), ev)] == []
        assert [c.text for c in rc.get_package_completions(Document("df$st", 5), ev)] == []
        assert [c.text for c in rc.get_package_completions(Document('"stats', 6), ev)] == []
        assert [c.text for c in rc.get_package_completions(Document('library("stats', 14), ev)] == ["stats"]
        assert [c.text for c in rc.get_package_completions(Document("stats", 5), ev)] == ["stats::"]
    finally:
        completion_mod.installed_packages = orig_installed

    spc = SmartPathCompleter()
    list(spc.get_completions(Document('cd "unclosed', 12), ev))

    terminal.write("cd\n")
    terminal.previous_line(2).strip().lower().assert_equal(
        os.path.realpath(os.path.expanduser("~")).lower()
    )
    terminal.write("cd -\n")
    terminal.previous_line(2).strip().assert_equal(os.getcwd())
    terminal.current_line().assert_startswith("#!>")




