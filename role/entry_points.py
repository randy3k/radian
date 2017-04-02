from .runtime import Rinstance
from .repl import create_r_repl


def main():
    runtime = Rinstance()
    runtime.run()
    application = create_r_repl()
    application.run()
