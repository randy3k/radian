from __future__ import unicode_literals
import sys
from helpers import assert_equal, assert_startswith, screen_process

radian_command = [sys.executable, "-m", "radian", "--coverage"]


def test_startup():

    with screen_process(radian_command) as (screen, process):
        assert_startswith(lambda: screen.display[0], "R ")
        assert_equal(lambda: (screen.cursor.x, screen.cursor.y), (4, 3))
        assert_startswith(lambda: screen.display[3], "r$>")
        process.write(b"\n")
        assert_startswith(lambda: screen.display[5], "r$>")
        assert_equal(lambda: (screen.cursor.x, screen.cursor.y), (4, 5))
        process.sendintr()
        assert_startswith(lambda: screen.display[7], "r$>")
        assert_equal(lambda: (screen.cursor.x, screen.cursor.y), (4, 7))
        process.write(b"q()\n")
        assert_equal(lambda: process.isalive(), False)


def test_version():
    with screen_process(radian_command + ["--version"]) as (screen, process):
        assert_startswith(lambda: screen.display[0], "radian version: ")
        import radian
        assert screen.display[0][16:].strip() == radian.__version__
