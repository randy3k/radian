from __future__ import unicode_literals
from .utils import assert_startswith


def test_shell(radian_terminal):
    screen = radian_terminal.screen
    assert_startswith(lambda: screen.display[3], "r$>")
    radian_terminal.write(b";")
    assert_startswith(lambda: screen.display[3], "#!>")
    radian_terminal.write(b"python --version\n")
    assert_startswith(lambda: screen.display[4], "Python ")
    assert_startswith(lambda: screen.display[6], "#!>")
    radian_terminal.write(b"\b")
    assert_startswith(lambda: screen.display[6], "r$>")
