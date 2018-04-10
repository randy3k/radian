from __future__ import unicode_literals
import optparse
import os
import sys
import re
import subprocess
from .util import read_registry


__version__ = '0.1.4'


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

    options, args = parser.parse_args()

    if 'R_HOME' not in os.environ:
        try:
            r_home = subprocess.check_output(["R", "RHOME"]).decode("utf-8").strip()
        except Exception:
            r_home = ""
        try:
            if sys.platform.startswith("win") and not r_home:
                r_binary = os.path.join(
                    read_registry("Software\\R-Core\\R", "InstallPath")[0],
                    "bin",
                    "R.exe")
                r_home = subprocess.check_output([r_binary, "RHOME"]).decode("utf-8").strip()
        except Exception:
            r_home = ""

        if r_home:
            os.environ['R_HOME'] = r_home
    else:
        r_home = os.environ['R_HOME']

    if options.version:
        if r_home:
            r_binary = os.path.normpath(os.path.join(r_home, "bin", "R"))
            try:
                version_output = subprocess.check_output(
                    [r_binary, "--version"], stderr=subprocess.STDOUT).decode("utf-8").strip()
                m = re.match(r"R version ([\.0-9]+)", version_output)
                if m:
                    r_version = m.group(1)
                else:
                    r_version = "NA"
            except Exception:
                r_version = "NA"
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
    os.environ["RETICULATE_PYTHON"] = sys.executable

    os.environ["R_DOC_DIR"] = os.path.join(r_home, "doc")
    os.environ["R_INCLUDE_DIR"] = os.path.join(r_home, "include")
    os.environ["R_SHARE_DIR"] = os.path.join(r_home, "share")

    if not r_home:
        raise RuntimeError("Cannot find R binary. Expose it via the `PATH` variable.")

    if sys.platform.startswith("win"):
        libR_dir = os.path.join(r_home, "bin", "x64" if sys.maxsize > 2**32 else "i386")

        # make sure Rblas.dll can be reached
        try:
            from ctypes import cdll, c_char_p
            msvcrt = cdll.msvcrt
            msvcrt.getenv.restype = c_char_p
            path = msvcrt.getenv("PATH".encode("utf-8"))
            path = libR_dir + ";" + path.decode("utf-8")
            msvcrt._putenv("PATH={}".format(path).encode("utf-8"))
        except Exception:
            pass

    from .deps import dependencies_loaded

    if not dependencies_loaded:
        print("Dependencies not loaded.")
        return

    from .rtichokeapp import RtichokeApplication
    RtichokeApplication(r_home).run(options)
