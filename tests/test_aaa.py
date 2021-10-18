def test_aaa(terminal):
    # just make sure radian has started.
    terminal.current_line().assert_startswith("r$>", timeout=10)
