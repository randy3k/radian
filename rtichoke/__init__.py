from __future__ import unicode_literals
import optparse
import os
import sys
from rapi.utils import which_rhome, rversion2


__version__ = '0.2.0.dev0'


def main():
    parser = optparse.OptionParser("usage: rtichoke")
    parser.add_option("-v", "--version", action="store_true", dest="version", help="get version")
    parser.add_option("--no-environ", action="store_true", dest="no_environ", help="Don't read the site and user environment files")
    parser.add_option("--no-site-file", action="store_true", dest="no_site_file", help="Don't read the site-wide Rprofile")
    parser.add_option("--no-init-file", action="store_true", dest="no_init_file", help="Don't read the user R profile")
    parser.add_option("--local-history", action="store_true", dest="local_history", help="Force using local history file")
    parser.add_option("--global-history", action="store_true", dest="global_history", help="Force using global history file")
    parser.add_option("--no-history", action="store_true", dest="no_history", help="Don't load any history files")
    parser.add_option("--vanilla", action="store_true", dest="vanilla", help="Combine --no-history --no-environ --no-site-file --no-init-file")
    parser.add_option("--ask-save", action="store_true", dest="ask_save", help="Ask to save R data")
    parser.add_option("--restore-data", action="store_true", dest="restore_data", help="Restore previously saved objects")
    parser.add_option("--debug", action="store_true", dest="debug", help="Debug mode")

    options, args = parser.parse_args()

    r_home = which_rhome()

    if options.version:
        if r_home:
            r_binary = os.path.normpath(os.path.join(r_home, "bin", "R"))
            r_version = rversion2(r_home)
        else:
            r_binary = "NA"
            r_version = "NA"
        print("rtichoke version: {}".format(__version__))
        print("r executable: {}".format(r_binary))
        print("r version: {}".format(r_version))
        print("python executable: {}".format(sys.executable))
        print("python version: {:d}.{:d}.{:d}".format(
            sys.version_info.major,
            sys.version_info.minor,
            sys.version_info.micro))
        return

    os.environ["RTICHOKE_VERSION"] = __version__
    os.environ["RTICHOKE_COMMAND_ARGS"] = " ".join(
        ["--" + k.replace("_", "-") for k, v in options.__dict__.items() if v])

    if not r_home:
        raise RuntimeError("Cannot find R binary. Expose it via the `PATH` variable.")

    from .rtichokeapp import RtichokeApplication
    RtichokeApplication(r_home).run(options)
