import os
import sys

import subprocess


def should_set_ld_library_path(r_home):
    lib_path = os.path.join(r_home, "lib")
    return (
        "R_LD_LIBRARY_PATH" not in os.environ
        or lib_path not in os.environ["R_LD_LIBRARY_PATH"]
    )


def set_ld_library_path(r_home):
    # respect R_ARCH variable?
    lib_path = os.path.join(r_home, "lib")
    ldpaths = os.path.join(r_home, "etc", "ldpaths")

    if os.path.exists(ldpaths):
        R_LD_LIBRARY_PATH = (
            subprocess.check_output(
                '. "{}"; echo $R_LD_LIBRARY_PATH'.format(ldpaths),
                shell=True,
            )
            .decode("utf-8")
            .strip()
        )
    elif "R_LD_LIBRARY_PATH" in os.environ:
        R_LD_LIBRARY_PATH = os.environ["R_LD_LIBRARY_PATH"]
    else:
        R_LD_LIBRARY_PATH = lib_path
    if lib_path not in R_LD_LIBRARY_PATH:
        R_LD_LIBRARY_PATH = "{}:{}".format(lib_path, R_LD_LIBRARY_PATH)
    os.environ["R_LD_LIBRARY_PATH"] = R_LD_LIBRARY_PATH
    if sys.platform == "darwin":
        ld_library_var = "DYLD_FALLBACK_LIBRARY_PATH"
    else:
        ld_library_var = "LD_LIBRARY_PATH"
    if ld_library_var in os.environ:
        LD_LIBRARY_PATH = "{}:{}".format(R_LD_LIBRARY_PATH, os.environ[ld_library_var])
    else:
        LD_LIBRARY_PATH = R_LD_LIBRARY_PATH
    os.environ[ld_library_var] = LD_LIBRARY_PATH

    if sys.platform == "darwin":
        # pythons load a version of Blas, we need to inject RBlas directly
        set_dyld_insert_blas_dylib(r_home)


def get_blas_dylib_path(r_home):
    if not sys.platform == "darwin":
        return None

    import lief

    lib_path = os.path.join(r_home, "lib")
    libr_path = os.path.join(lib_path, "libR.dylib")
    if not os.path.exists(libr_path):
        return None

    try:
        lief_res = lief.parse(os.path.realpath(libr_path))
        for cmd in lief_res.commands:
            if cmd.command == lief.MachO.LoadCommand.TYPE.LOAD_DYLIB and cmd.name.endswith(
                "libRblas.dylib"
            ):
                return cmd.name
    except Exception:
        pass

    # best effort
    return os.path.join(lib_path, "libRBlas.dylib")


def set_dyld_insert_blas_dylib(r_home):
    if not sys.platform == "darwin":
        return
    libr_blas_dylib = get_blas_dylib_path(r_home)
    if not os.path.exists(libr_blas_dylib):
        return

    if "DYLD_INSERT_LIBRARIES" not in os.environ:
        os.environ["DYLD_INSERT_LIBRARIES"] = libr_blas_dylib
    else:
        os.environ["DYLD_INSERT_LIBRARIES"] = "{}:{}".format(
            os.environ["DYLD_INSERT_LIBRARIES"], libr_blas_dylib
        )
    os.environ["R_DYLD_INSERT_LIBRARIES"] = libr_blas_dylib


def reset_dyld_insert_blas_dylib():
    if not sys.platform == "darwin":
        return
    if "DYLD_INSERT_LIBRARIES" not in os.environ or "R_DYLD_INSERT_LIBRARIES" not in os.environ:
        return
    
    lib = os.environ["DYLD_INSERT_LIBRARIES"]
    lib = lib.replace(os.environ["R_DYLD_INSERT_LIBRARIES"], "")
    if lib == "":
        del os.environ["DYLD_INSERT_LIBRARIES"]

    del os.environ["R_DYLD_INSERT_LIBRARIES"]
