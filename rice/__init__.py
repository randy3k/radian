from __future__ import unicode_literals
import optparse
import os
import sys
import subprocess

from .deps import dependencies_loaded

__version__ = '0.0.43.dev1'


def main():
    if not dependencies_loaded:
        print("Dependencies not loaded.")
        return

    parser = optparse.OptionParser("usage: rice")
    parser.add_option("-v", "--version", action="store_true", dest="version", help="get version")
    parser.add_option("--no-environ", action="store_true", dest="no_environ", help="Don't read the site and user environment files")
    parser.add_option("--no-site-file", action="store_true", dest="no_site_file", help="Don't read the site-wide Rprofile")
    parser.add_option("--no-init-file", action="store_true", dest="no_init_file", help="Don't read the user R profile")
    parser.add_option("--local-history", action="store_true", dest="local_history", help="Force using local history file")
    parser.add_option("--global-history", action="store_true", dest="global_history", help="Force using global history file")
    parser.add_option("--no-history", action="store_true", dest="no_history", help="Don't load any history files")
    parser.add_option("--vanilla", action="store_true", dest="vanilla", help="Combine --no-history --no-environ --no-site-file --no-init-file")

    options, args = parser.parse_args()

    if options.version:
        print("rice version: {}".format(__version__))
        print("python version: {:d}.{:d}.{:d}".format(
            sys.version_info.major,
            sys.version_info.minor,
            sys.version_info.micro))
        print("python executable: {}".format(sys.executable))
        return

    os.environ["RICE_VERSION"] = __version__
    os.environ["RICE_COMMAND_ARGS"] = " ".join(
        ["--" + k.replace("_", "-") for k, v in options.__dict__.items() if v])
    os.environ["RETICULATE_PYTHON"] = sys.executable

    from .riceapp import RiceApplication

    if 'R_HOME' not in os.environ:
        try:
            r_home = subprocess.check_output(["R", "RHOME"]).decode("utf-8").strip()
        except FileNotFoundError:
            r_home = ""
        if not r_home:
            raise RuntimeError("Cannot find R binary. Expose it via the `PATH` variable.")
        os.environ['R_HOME'] = r_home
    else:
        r_home = os.environ['R_HOME']

    os.environ["R_DOC_DIR"] = os.path.join(r_home, "doc")
    os.environ["R_INCLUDE_DIR"] = os.path.join(r_home, "include")
    os.environ["R_SHARE_DIR"] = os.path.join(r_home, "share")

    RiceApplication(r_home).run(options)
