from __future__ import unicode_literals
import sys
from helpers import assert_equal, assert_startswith, PtyProcess, Screen, ByteStream


def test_startup():
    p = PtyProcess.spawn([sys.executable, "-m", "rtichoke"])
    screen = Screen(p, 80, 24)
    stream = ByteStream(screen)
    stream.start_feeding()

    try:
        assert_startswith(lambda: screen.display[0], "R ")
        assert_equal(lambda: (screen.cursor.x, screen.cursor.y), (4, 3))
        assert_startswith(lambda: screen.display[3], "r$>")
    finally:
        p.terminate(force=True)
