import os
import subprocess
from ctypes import c_char_p, c_int, c_void_p, CDLL
from ctypes.util import find_library
from .util import ccall


class Rinstance(object):
    libR = None
    is_busy = False
    rinstance = None
    offset = None

    def __init__(self):
        if 'R_HOME' not in os.environ:
            Rhome = subprocess.check_output(["R", "RHOME"]).decode("utf-8").strip()
            os.environ['R_HOME'] = Rhome
        os.environ["R_DOC_DIR"] = os.path.join(Rhome, "doc")
        os.environ["R_INCLUDE_DIR"] = os.path.join(Rhome, "include")
        os.environ["R_SHARE_DIR"] = os.path.join(Rhome, "share")
        Rinstance.libR = CDLL(find_library("R"))

    def run(self):
        _argv = ["ride", "--no-save", "--quiet"]
        argn = len(_argv)
        argv = (c_char_p * argn)()
        for i, a in enumerate(_argv):
            argv[i] = c_char_p(a.encode('utf-8'))

        Rinstance.libR.Rf_initEmbeddedR(argn, argv)

        s = ccall("Rf_ScalarInteger", Rinstance.libR, c_void_p, [c_int], 0)
        Rinstance.offset = ccall("INTEGER", Rinstance.libR, c_void_p, [c_void_p], s).value - s.value
