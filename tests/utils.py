import time


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
