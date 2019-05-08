from __future__ import unicode_literals
import os
import tempfile
try:
    from shlex import quote
except ImportError:
    from pipes import quote
from .utils import assert_equal, assert_startswith, assert_contains


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
    radian_terminal.write(b";")
    tdir = tempfile.mkdtemp()
    radian_terminal.write("cd {}\n".format(quote(tdir)).encode('utf-8'))
    base = os.path.basename(tdir)
    assert_contains(lambda: screen.display[7], os.sep + base)
    radian_terminal.write(b"cd -\n")
    assert_equal(lambda: screen.display[10].strip(), os.getcwd())
