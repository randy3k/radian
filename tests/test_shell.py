from __future__ import unicode_literals
import os
from .utils import assert_equal, assert_startswith, assert_endswith


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


def test_cd(radian_terminal):
    screen = radian_terminal.screen
    assert_startswith(lambda: screen.display[3], "r$>")
    radian_terminal.write(b";")
    d = os.path.realpath(os.path.join(os.path.dirname(__file__), "..", "radi"))
    radian_terminal.write("cd {}".format(d).encode('utf-8'))
    assert_endswith(lambda: screen.display[3].strip(), os.sep + "radi")
    radian_terminal.write(b"\t")
    assert_endswith(lambda: screen.display[3].strip(), os.sep + "radian")
    radian_terminal.write(b"\n")
    assert_endswith(lambda: screen.display[4].strip(), os.sep + "radian")
    radian_terminal.write(b"cd -\n")
    assert_equal(lambda: screen.display[7].strip(), os.getcwd())


def test_cd2(radian_terminal):
    screen = radian_terminal.screen
    assert_startswith(lambda: screen.display[3], "r$>")
    radian_terminal.write(b";")
    d = os.path.realpath(os.path.join(os.path.dirname(__file__), "..", "radi"))
    radian_terminal.write("cd \"{}".format(d).encode('utf-8'))
    assert_endswith(lambda: screen.display[3].strip(), os.sep + "radi")
    radian_terminal.write(b"\t")
    assert_endswith(lambda: screen.display[3].strip(), os.sep + "radian")
    radian_terminal.write(b"\"\n")
    assert_endswith(lambda: screen.display[4].strip(), os.sep + "radian")
    radian_terminal.write(b"cd -\n")
    assert_equal(lambda: screen.display[7].strip(), os.getcwd())
