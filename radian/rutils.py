import os
import sys
from rchitect import rcall, rcopy
from rchitect.interface import roption


# =============================================================================
# 1. Package Inspection & Caching
# =============================================================================

_installed_packages_cache = (None, [])


def installed_packages():
    global _installed_packages_cache
    try:
        lib_paths = rcopy(list, rcall(("base", ".libPaths")))
        key = tuple(
            (p, os.stat(p).st_mtime if os.path.isdir(p) else None)
            for p in lib_paths
        )
        if _installed_packages_cache[0] != key:
            pkgs = rcopy(list, rcall(("base", ".packages"), **{"all.available": True}))
            _installed_packages_cache = (key, pkgs)
        return _installed_packages_cache[1]
    except Exception:
        return []


# =============================================================================
# 2. Profile & Hook Loading
# =============================================================================


def source_file(path):
    rcall(("base", "source"), path, rcall(("base", "new.env")))


def make_path(*p):
    return os.path.realpath(os.path.normpath(os.path.expanduser(os.path.join(*p))))


def user_path(*args):
    return make_path(rcall(("base", "path.expand"), "~", _convert=True), *args)


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


def run_on_load_hooks():
    hooks = roption("radian.on_load_hooks", [])
    for hook in hooks:
        hook()


# =============================================================================
# 3. Session Lifecycle Helpers
# =============================================================================


def register_cleanup(cleanup):
    rcall(
        ("base", "reg.finalizer"),
        rcall(("base", "getOption"), "rchitect.py_tools"),
        cleanup,
        onexit=True,
    )

