__version__ = "0.8.0"

__all__ = ["get_app", "main"]


def get_app():
    from .app import get_app as _get_app

    return _get_app()


def main(cleanup=None):
    from .__main__ import main as _main

    return _main(cleanup=cleanup)
