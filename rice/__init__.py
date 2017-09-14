from __future__ import unicode_literals
import optparse
import os

from . import deps
from .application import RiceApplication

__version__ = '0.0.13'


def main():
    parser = optparse.OptionParser("usage: rice")
    parser.add_option("-v", "--version", action="store_true", dest="version", help="get version")
    parser.add_option("--no-environ", action="store_true", dest="no_environ", help="Don't read the site and user environment files")
    parser.add_option("--no-site-file", action="store_true", dest="no_site_file", help="Don't read the site-wide Rprofile")
    parser.add_option("--no-init-file", action="store_true", dest="no_init_file", help="Don't read the user R profile")
    parser.add_option("--vanilla", action="store_true", dest="vanilla", help="Combine --no-environ --no-site-file --no-init-file")

    options, args = parser.parse_args()

    if options.version:
        print("version {}".format(__version__))
        return

    os.environ["RICE_VERSION"] = __version__

    no_environ = options.no_environ
    no_site_file = options.no_site_file
    no_init_file = options.no_init_file

    if options.vanilla:
        no_environ = True
        no_site_file = True
        no_init_file = True

    if no_environ:
        os.environ["R_ENVIRON"] = ""
        os.environ["R_ENVIRON_USER"] = ""

    if no_site_file:
        os.environ["R_PROFILE"] = ""

    if no_init_file:
        os.environ["R_PROFILE_USER"] = ""

    RiceApplication().run()
