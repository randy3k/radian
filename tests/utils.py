from __future__ import unicode_literals
import time
import six
import operator


def assert_op(x, y, op, timeout=5):
    t = time.time()
    f = x if callable(x) else lambda: x
    g = y if callable(y) else lambda: y
    while not op(f(), g()):
        if time.time() - t > timeout:
            raise Exception(
                "{}: arguments {} and {}".format(str(op), str(f()), str(g())))
        time.sleep(0.01)


def assert_equal(x, y, timeout=5):
    assert_op(x, y, operator.eq, timeout)


def assert_startswith(x, y, timeout=5):
    assert_op(x, y, six.text_type.startswith, timeout)
