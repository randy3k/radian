from __future__ import unicode_literals
import os
import sys
from rchitect import rcopy, rcall, reval
from rchitect._cffi import ffi, lib
from rchitect.interface import protected, rstring_p


def prase_text_complete(text):
    status = ffi.new("ParseStatus[1]")
    s = rstring_p(text)
    orig_stderr = sys.stderr
    sys.stderr = None
    with protected(s):
        lib.R_ParseVector(s, -1, status, lib.R_NilValue)
        sys.stderr = orig_stderr
    return status[0] != 2


def package_is_loaded(pkg):
    return pkg in rcopy(rcall(("base", "loadedNamespaces")))


def package_is_installed(pkg):
    return pkg in rcopy(reval("rownames(installed.packages())"))


def execute_key_bindings_script(*args):
    rcall(
        ("base", "source"),
        os.path.join(os.path.dirname(__file__), "R", "key_bindings.R"),
        rcall("new.env"))


def finalizer(cleanup):
    rcall(("base", "reg.finalizer"),
          rcall(("base", "getOption"), "rchitect.py_tools"),
          cleanup,
          onexit=True)
