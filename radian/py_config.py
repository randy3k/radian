import sys
import ctypes
import ctypes.util

if sys.version < '3.4':
    import imp

    def module_exists(name):
        try:
            imp.find_module(name)
            return True
        except ImportError:
            return False
else:
    import importlib.util

    def module_exists(name):
        if importlib.util.find_spec(name):
            return True
        else:
            return False


def config():
    if sys.platform.startswith("win"):
        return

    libdl = ctypes.CDLL(ctypes.util.find_library('dl'))
    libc = ctypes.PyDLL(None)

    class Dl_info(ctypes.Structure):
        _fields_ = (('dli_fname', ctypes.c_char_p),
                    ('dli_fbase', ctypes.c_void_p),
                    ('dli_sname', ctypes.c_char_p),
                    ('dli_saddr', ctypes.c_void_p))

    libdl.dladdr.argtypes = (ctypes.c_void_p, ctypes.POINTER(Dl_info))
    info = Dl_info()
    libdl.dladdr(libc.Py_IsInitialized, ctypes.byref(info))

    python = sys.executable
    libpython = info.dli_fname.decode()
    try:
        import sysconfig
        pythonhome = sysconfig.get_config_vars('prefix')[0] + ":" + \
            sysconfig.get_config_vars('exec_prefix')[0]
    except Exception:
        pythonhome = None
    numpy = module_exists("numpy")

    return (python, libpython, pythonhome, numpy)
