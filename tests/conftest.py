import pytest
import sys
import time
from .terminal import open_terminal


def pytest_addoption(parser):
    parser.addoption(
        "--coverage", action="store_true", default=False, help="generate coverage report"
    )


@pytest.fixture(scope='session')
def radian_command(pytestconfig):
    if pytestconfig.getoption("coverage"):
        radian_command = [sys.executable, "-m", "radian", "--coverage"]
    else:
        radian_command = [sys.executable, "-m", "radian"]

    return radian_command


@pytest.fixture(scope='function')
def radian_terminal(radian_command):
    with open_terminal(radian_command) as terminal:
        yield terminal
        terminal.write(b"q()\n")
        start_time = time.time()
        while terminal.isalive():
            if time.time() - start_time > 5:
                raise Exception("radian didn't quit cleanly")
            time.sleep(0.01)
