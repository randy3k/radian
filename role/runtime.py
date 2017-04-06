import os
import subprocess
import sys
from ctypes import c_char_p, c_int, c_void_p, CDLL
from .util import ccall


class Rinstance(object):
    libR = None
    offset = None

    def __init__(self):
        if 'R_HOME' not in os.environ:
            Rhome = subprocess.check_output(["R", "RHOME"]).decode("utf-8").strip()
            os.environ['R_HOME'] = Rhome
        else:
            Rhome = os.environ['R_HOME']
        os.environ["R_DOC_DIR"] = os.path.join(Rhome, "doc")
        os.environ["R_INCLUDE_DIR"] = os.path.join(Rhome, "include")
        os.environ["R_SHARE_DIR"] = os.path.join(Rhome, "share")
        if sys.platform == "win32":
            libR_path = os.path.join(Rhome, "bin", ['i386', 'x64'][sys.maxsize > 2**32], "R.dll")
        elif sys.platform == "darwin":
            libR_path = os.path.join(Rhome, "lib", "libR.dylib")
        elif sys.platform.startswith("linux"):
            libR_path = os.path.join(Rhome, "lib", "libR.so")

        if not os.path.exists(libR_path):
            raise RuntimeError("Cannot locate R share library.")

        self.libR = CDLL(libR_path)

        _argv = ["role", "--no-save", "--quiet"]
        argn = len(_argv)
        argv = (c_char_p * argn)()
        for i, a in enumerate(_argv):
            argv[i] = c_char_p(a.encode('utf-8'))

        self.libR.Rf_initEmbeddedR(argn, argv)

        s = ccall("Rf_ScalarInteger", self.libR, c_void_p, [c_int], 0)
        self.offset = ccall("INTEGER", self.libR, c_void_p, [c_void_p], s).value - s.value
