import ctypes
import os
import subprocess
import sys


class _Dl_info(ctypes.Structure):
    _fields_ = [
        ("dli_fname", ctypes.c_char_p),
        ("dli_fbase", ctypes.c_void_p),
        ("dli_sname", ctypes.c_char_p),
        ("dli_saddr", ctypes.c_void_p),
    ]


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
    if sys.platform != "darwin":
        return None

    lib_path = os.path.join(r_home, "lib")
    libr_path = os.path.join(lib_path, "libR.dylib")
    if not os.path.exists(libr_path):
        return None

    try:
        libc = ctypes.CDLL(None)
        libc.dlsym.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
        libc.dlsym.restype = ctypes.c_void_p
        libc.dladdr.argtypes = [ctypes.c_void_p, ctypes.POINTER(_Dl_info)]
        libc.dladdr.restype = ctypes.c_int

        libr = ctypes.CDLL(os.path.realpath(libr_path))
        addr = libc.dlsym(libr._handle, b"dgemm_")
        info = _Dl_info()
        if addr and libc.dladdr(addr, ctypes.byref(info)) and info.dli_fname:
            return os.fsdecode(info.dli_fname)
    except Exception:
        pass

    # best effort
    return os.path.join(lib_path, "libRblas.dylib")


def set_dyld_insert_blas_dylib(r_home):
    if sys.platform != "darwin":
        return
    libr_blas_dylib = get_blas_dylib_path(r_home)
    if not libr_blas_dylib or not os.path.exists(libr_blas_dylib):
        return

    if "DYLD_INSERT_LIBRARIES" not in os.environ:
        os.environ["DYLD_INSERT_LIBRARIES"] = libr_blas_dylib
    else:
        os.environ["DYLD_INSERT_LIBRARIES"] = "{}:{}".format(
            os.environ["DYLD_INSERT_LIBRARIES"], libr_blas_dylib
        )
    os.environ["R_DYLD_INSERT_LIBRARIES"] = libr_blas_dylib


def reset_dyld_insert_blas_dylib():
    if sys.platform != "darwin":
        return
    if (
        "DYLD_INSERT_LIBRARIES" not in os.environ
        or "R_DYLD_INSERT_LIBRARIES" not in os.environ
    ):
        return

    r_dylib = os.environ.pop("R_DYLD_INSERT_LIBRARIES")
    libs = [
        lib
        for lib in os.environ["DYLD_INSERT_LIBRARIES"].split(":")
        if lib and lib != r_dylib
    ]
    if libs:
        os.environ["DYLD_INSERT_LIBRARIES"] = ":".join(libs)
    else:
        del os.environ["DYLD_INSERT_LIBRARIES"]


def maybe_reexec(r_home):
    if sys.platform == "darwin":
        # avoid libRBlas to propagate downstream
        reset_dyld_insert_blas_dylib()

    reexec_args = (
        (["-P"] if sys.version_info >= (3, 11) else [])
        + ["-m", "radian"]
        + sys.argv[1:]
    )
    if not sys.platform.startswith("win"):
        if should_set_ld_library_path(r_home):
            set_ld_library_path(r_home)
            os.execv(sys.executable, [sys.executable] + reexec_args)
    else:
        from rchitect.utils import should_use_utf8_host, exec_utf8_host

        if should_use_utf8_host(r_home):
            exec_utf8_host(reexec_args)
