import os
import sys
from rchitect import rcopy, reval, rcall
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


def make_path(*p):
    return os.path.realpath(os.path.normpath(os.path.expanduser(os.path.join(*p))))


def user_path(*args):
    return make_path(rcopy(rcall(("base", "path.expand"), "~")), *args)


def source_radian_profile(path):
    if path:
        path = os.path.expanduser(path)
        if os.path.exists(path):
            source_file(path)
    else:
        if "XDG_CONFIG_HOME" in os.environ:
            xdg_profile = make_path(os.environ["XDG_CONFIG_HOME"], "radian", "profile")
        elif not sys.platform.startswith("win"):
            xdg_profile = make_path("~", ".config", "radian", "profile")
        else:
            xdg_profile = make_path("~", "radian", "profile")

        if os.path.exists(xdg_profile):
            source_file(xdg_profile)

        global_profile = make_path("~", ".radian_profile")
        local_profile = make_path(".radian_profile")

        if os.path.exists(global_profile):
            source_file(global_profile)
        elif sys.platform.startswith("win"):
            # for backward compatibility
            global_profile = user_path(".radian_profile")
            if os.path.exists(global_profile):
                source_file(global_profile)

        if os.path.exists(local_profile) and local_profile != global_profile:
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


def set_lang():
    if sys.platform.startswith("win"):
        if not os.environ.get("LANG", ""):
            if rcopy(reval(
                   'compareVersion(paste0(R.version$major, ".", R.version$minor), "4.2.0") >= 0')):
                os.environ["LANG"] = "en_US.UTF-8"


def run_on_load_hooks():
    hooks = roption("radian.on_load_hooks", [])
    for hook in hooks:
        hook()
