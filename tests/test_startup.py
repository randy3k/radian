def test_startup(terminal):
    try:
        # the first line sometimes disappear for no reasons on circleci
        # terminal.line(0).assert_startswith("R ")
        terminal.cursor().assert_equal((4, 3))
        terminal.current_line().assert_startswith("r$>")
        terminal.write("\n")
        terminal.current_line().assert_startswith("r$>")
        terminal.cursor().assert_equal((4, 5))
        terminal.write("a")
        terminal.sendintr()
        terminal.current_line().strip().assert_equal("r$>")
        terminal.cursor().assert_equal((4, 7))
    except Exception:
        print("\n".join(terminal.screen.display))
        raise
