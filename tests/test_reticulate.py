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
    terminal.write("d = {'a': 1}\n")
    terminal.current_line().strip().assert_equal(">>>")
    terminal.write("d['a']\n")
    terminal.previous_line(2).strip().assert_equal("1")
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
    terminal.write("1 + \\\nc\n")
    terminal.previous_line(2).strip().assert_equal("4")
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


def test_reticulate_completion_unit():
    import __main__
    from prompt_toolkit.completion import CompleteEvent
    from prompt_toolkit.document import Document
    from radian.reticulate import PythonCompleter

    __main__.sys_test_mod = __import__("sys")
    try:
        completer = PythonCompleter()
        typing_event = CompleteEvent(completion_requested=False)
        tab_event = CompleteEvent(completion_requested=True)

        # Adjacent punctuation, comments, trailing dots, and exact matches do NOT pop up completions while typing
        for text in [
            "x = robject({",
            "x = robject({'a':",
            "d = {'a':",
            "a ==",
            "# comment",
            "sys_test_mod.",
            "pass",
        ]:
            comps = [
                c.text
                for c in completer.get_completions(Document(text, len(text)), typing_event)
            ]
            assert comps == [], f"unexpected completions for {text!r}: {comps}"

        assert "import" not in [
            c.text
            for c in completer.get_completions(Document("import", 6), typing_event)
        ]

        # Comments do not complete even on <Tab>, whereas '#' inside a string literal is not a comment
        assert list(completer.get_completions(Document("# sys_test", 10), tab_event)) == []
        assert list(completer.get_completions(Document("x = 1 # sys_test", 16), tab_event)) == []
        assert "path" in [
            c.text
            for c in completer.get_completions(
                Document('s = "# not comment"; sys_test_mod.', 34), tab_event
            )
        ]

        # Dotted attribute with >= 1 char after dot DOES auto-complete while typing
        comps_typing = [
            c.text
            for c in completer.get_completions(
                Document("sys_test_mod.pa", 15), typing_event
            )
        ]
        assert "path" in comps_typing
        comps_one_char = [
            c.text
            for c in completer.get_completions(
                Document("sys_test_mod.p", 14), typing_event
            )
        ]
        assert "path" in comps_one_char

        # Trailing dot DOES complete when <Tab> is pressed
        comps_tab = [
            c.text
            for c in completer.get_completions(Document("sys_test_mod.", 13), tab_event)
        ]
        assert "path" in comps_tab

        # Exact match on attribute closes popup
        assert [
            c.text
            for c in completer.get_completions(
                Document("sys_test_mod.maxsize", 20), typing_event
            )
        ] == []

        # 1-char escape inside string does not trigger LaTeX completion while typing, 2-char does
        assert list(completer.get_completions(Document(r'"hello\n', 8), typing_event)) == []
        assert any(
            c.text == "α"
            for c in completer.get_completions(Document(r"\al", 3), typing_event)
        )
    finally:
        del __main__.sys_test_mod


def test_reticulate_multiline_and_keybindings_unit(monkeypatch):
    import signal
    from prompt_toolkit.document import Document
    from pygments.token import Punctuation
    from radian.key_bindings import RAW_STRING_PREFIX_RE, create_prompt_key_bindings
    from radian.reticulate import (
        _tokenize_python_before_cursor,
        handle_multiline_code,
        parse_text_complete,
    )

    # 1. handle_multiline_code catches KeyboardInterrupt and restores SIGINT handler
    messages = []
    monkeypatch.setattr(
        "radian.reticulate.rcall", lambda fn, msg: messages.append((fn, msg))
    )
    orig_sigint = signal.getsignal(signal.SIGINT)
    handle_multiline_code("if True:\n    raise KeyboardInterrupt()\n")
    assert messages == [(("base", "message"), "KeyboardInterrupt")]
    assert signal.getsignal(signal.SIGINT) == orig_sigint

    # 2. Token-based colon check only matches real Python Punctuation colons,
    # not colons at the end of comments or unclosed string literals
    def is_python_colon(text):
        doc = Document(text, len(text))
        if not doc.current_line_before_cursor.endswith(":"):
            return False
        tokens = _tokenize_python_before_cursor(doc)
        return bool(tokens) and tokens[-1][1] in Punctuation

    assert is_python_colon("def f():")
    assert is_python_colon("if True:\n    for x in y:")
    assert not is_python_colon("x = 1 # note:")
    assert not is_python_colon('x = "http:')

    # 3. RAW_STRING_PREFIX_RE is anchored to standalone r/R prefix and create_prompt_key_bindings
    # does not bind R raw-string delimiter pairs in Python mode
    assert RAW_STRING_PREFIX_RE.match('r"-') is not None
    assert RAW_STRING_PREFIX_RE.match('x <- r"--') is not None
    assert RAW_STRING_PREFIX_RE.match('var"-') is None
    assert RAW_STRING_PREFIX_RE.match('df$r"-') is None

    pkb = create_prompt_key_bindings(parse_text_complete)
    assert not any(
        b.handler.__qualname__.startswith("_insert_raw_string_pair")
        for b in pkb.bindings
    )
