from __future__ import unicode_literals
import os
import sys
from rchitect import rcopy, rcall
from rchitect._cffi import ffi, lib
from rchitect.interface import roption, protected, rstring_p
from .key_bindings import map_key
from .console import suppress_stderr


def prase_text_complete(text):
    status = ffi.new("ParseStatus[1]")
    s = rstring_p(text)
    orig_stderr = sys.stderr
    sys.stderr = None
    with protected(s), suppress_stderr():
        lib.R_ParseVector(s, -1, status, lib.R_NilValue)
        sys.stderr = orig_stderr
    return status[0] != 2


def package_is_loaded(pkg):
    return pkg in rcopy(rcall(("base", "loadedNamespaces")))


def package_is_installed(pkg):
    return pkg in installed_packages()


def installed_packages():
    try:
        return rcall(("base", ".packages"), **{"all.available": True, "_convert": True})
    except Exception:
        return []


def source_file(path):
    rcall(("base", "source"), path, rcall(("base", "new.env")))


def user_path(*args):
    return os.path.join(rcopy(rcall(("base", "path.expand"), "~")), *args)


def source_radian_profile(path):
    if path:
        path = os.path.expanduser(path)
        if os.path.exists(path):
            source_file(path)
    else:
        global_profile = os.path.realpath(os.path.normpath(user_path(".radian_profile")))
        local_profile = os.path.realpath(os.path.normpath(".radian_profile"))
        if global_profile and os.path.exists(global_profile):
            source_file(global_profile)
        if local_profile and os.path.exists(local_profile) and local_profile != global_profile:
            source_file(local_profile)

def load_custom_key_bindings(*args):
    esc_keymap = roption("radian.escape_key_map", [])
    for m in esc_keymap:
        map_key(("escape", m["key"]), m["value"], mode=m["mode"] if "mode" in m else "r")


def register_cleanup(cleanup):
    rcall(("base", "reg.finalizer"),
          rcall(("base", "getOption"), "rchitect.py_tools"),
          cleanup,
          onexit=True)


def run_on_load_hooks():
    hooks = roption("radian.on_load_hooks", [])
    for hook in hooks:
        hook()
