from __future__ import unicode_literals
import sys
from helpers import assert_equal, assert_startswith, screen_process


def test_startup():
    rtichoke_command = [sys.executable, "-m", "rtichoke"]

    with screen_process(rtichoke_command) as (screen, process):
        assert_startswith(lambda: screen.display[0], "R ")
        assert_equal(lambda: (screen.cursor.x, screen.cursor.y), (4, 3))
        assert_startswith(lambda: screen.display[3], "r$>")
        process.write(b"\n")
        assert_startswith(lambda: screen.display[5], "r$>")
        assert_equal(lambda: (screen.cursor.x, screen.cursor.y), (4, 5))
        process.sendintr()
        assert_startswith(lambda: screen.display[7], "r$>")
        assert_equal(lambda: (screen.cursor.x, screen.cursor.y), (4, 7))

    with screen_process(rtichoke_command + ["--version"]) as (screen, process):
        assert_startswith(lambda: screen.display[0], "rtichoke version: ")
        import rtichoke
        assert screen.display[0][18:].strip() == rtichoke.__version__
