from __future__ import unicode_literals
import ctypes
from ctypes import c_char_p, c_void_p, cast
import sys
import shlex


def ccall(fname, lib, restype, argtypes, *args):
    f = getattr(lib, fname)
    f.restype = restype
    f.argtypes = argtypes
    res = f(*args)
    if restype == c_void_p or restype == c_char_p:
        return cast(res, restype)
    else:
        return res


def cglobal(vname, lib, vtype=c_void_p):
    return vtype.in_dll(lib, vname)


def is_ascii(s):
    return all(ord(c) < 128 for c in s)


def split_args(cmd):
    if sys.platform.startswith('win'):
        # https://stackoverflow.com/questions/33560364
        nargs = ctypes.c_int()
        ctypes.windll.shell32.CommandLineToArgvW.restype = ctypes.POINTER(ctypes.c_wchar_p)
        lpargs = ctypes.windll.shell32.CommandLineToArgvW(unicode(cmd), ctypes.byref(nargs))
        args = [lpargs[i] for i in range(nargs.value)]
        if ctypes.windll.kernel32.LocalFree(lpargs):
            raise AssertionError
        return args
    else:
        return shlex.split(cmd)
