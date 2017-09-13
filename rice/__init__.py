from __future__ import unicode_literals
import optparse
import os

from . import deps
from .application import RiceApplication

__version__ = '0.0.12'


def main():
    parser = optparse.OptionParser("usage: rice")
    parser.add_option("-v", "--version", action="store_true", dest="version", help="get version")

    options, args = parser.parse_args()

    if options.version:
        print("version {}".format(__version__))
        return

    os.environ["RICE_VERSION"] = __version__

    RiceApplication().run()
