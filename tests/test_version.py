import sys
from .terminal import open_terminal
from .utils import assert_startswith


def test_version():
    command = [sys.executable, "-m", "radian", "--version", "--coverage"]
    with open_terminal(command) as terminal:
        assert_startswith(lambda: terminal.screen.display[0], "radian version: ")
        import radian
        assert terminal.screen.display[0][16:].strip() == radian.__version__
