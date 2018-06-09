import sys
import pyte
import threading
import time
from contextlib import contextmanager

if sys.platform.startswith("win"):
    import winpty
else:
    import ptyprocess

__all__ = ["assert_equal", "assert_startswith", "PtyProcess", "Screen", "ByteStream"]


def assert_equal(x, y, timeout=5):
    t = time.time()
    f = x if callable(x) else lambda: x
    g = y if callable(y) else lambda: y
    while not f() == g():
        if time.time() - t > timeout:
            raise Exception("'{}' not equal to '{}'".format(f(), g()))
        time.sleep(0.01)


def assert_startswith(x, y, timeout=5):
    t = time.time()
    f = x if callable(x) else lambda: x
    g = y if callable(y) else lambda: y
    while not f().startswith(g()):
        if time.time() - t > timeout:
            raise Exception(
                "expect '{}', but got '{}'".format(g(), f().strip()))
        time.sleep(0.01)


if sys.platform.startswith("win"):
    ParentPtyProcess = winpty.PtyProcess
else:
    ParentPtyProcess = ptyprocess.PtyProcess


class PtyProcess(ParentPtyProcess):

    def read(self, nbytes):
        if sys.platform.startswith("win"):
            return super(PtyProcess, self).read(nbytes).encode("utf-8")
        else:
            return super(PtyProcess, self).read(nbytes)

    def write(self, data):
        if sys.platform.startswith("win"):
            super(PtyProcess, self).write(data.decode("utf-8"))
        else:
            super(PtyProcess, self).write(data)


class Screen(pyte.Screen):

    def __init__(self, process, *args, **kwargs):
        self._process = process
        super(Screen, self).__init__(*args, **kwargs)

    def write_process_input(self, data):
        self._process.write(data.encode("utf-8"))


class ByteStream(pyte.ByteStream):

    def start_feeding(self):
        screen = self.listener
        process = screen._process

        def reader():
            while True:
                try:
                    data = process.read(1024)
                except EOFError:
                    break
                if data:
                    self.feed(data)
        t = threading.Thread(target=reader)
        t.start()


@contextmanager
def screen_process(cmd):
    p = PtyProcess.spawn(cmd)
    screen = Screen(p, 80, 24)
    stream = ByteStream(screen)
    stream.start_feeding()
    try:
        yield screen, p
    finally:
        p.terminate(force=True)
