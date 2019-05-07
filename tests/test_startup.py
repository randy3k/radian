from __future__ import unicode_literals
from .utils import assert_equal, assert_startswith


def test_startup(radian_terminal):
    screen = radian_terminal.screen
    assert_startswith(lambda: screen.display[0], "R ")
    assert_equal(lambda: (screen.cursor.x, screen.cursor.y), (4, 3))
    assert_startswith(lambda: screen.display[3], "r$>")
    radian_terminal.write(b"\n")
    assert_startswith(lambda: screen.display[5], "r$>")
    assert_equal(lambda: (screen.cursor.x, screen.cursor.y), (4, 5))
    radian_terminal.sendintr()
    assert_startswith(lambda: screen.display[7], "r$>")
    assert_equal(lambda: (screen.cursor.x, screen.cursor.y), (4, 7))
