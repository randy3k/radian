from __future__ import unicode_literals
import os
import subprocess
import sys
import ctypes
from ctypes import c_char, c_char_p, c_int, c_size_t, c_void_p, \
    cast, addressof, pointer, CDLL, CFUNCTYPE, POINTER
from .util import ccall, cglobal


if sys.platform.startswith("win"):
    from ctypes import wintypes

    FlushConsoleInputBuffer = ctypes.windll.kernel32.FlushConsoleInputBuffer
    FlushConsoleInputBuffer.argtypes = [wintypes.HANDLE]
    FlushConsoleInputBuffer.restype = wintypes.BOOL

    GetStdHandle = ctypes.windll.kernel32.GetStdHandle
    GetStdHandle.argtypes = [wintypes.DWORD]
    GetStdHandle.restype = wintypes.HANDLE

    STD_INPUT_HANDLE = -10

    class RStart(ctypes.Structure):
        _fields_ = [
            ('R_Quiet', c_int),
            ('R_Slave', c_int),
            ('R_Interactive', c_int),
            ('R_Verbose', c_int),
            ('LoadSiteFile', c_int),
            ('LoadInitFile', c_int),
            ('DebugInitFile', c_int),
            ('RestoreAction', c_int),
            ('SaveAction', c_int),
            ('vsize', c_size_t),
            ('nsize', c_size_t),
            ('max_vsize', c_size_t),
            ('max_nsize', c_size_t),
            ('ppsize', c_size_t),
            ('NoRenviron', c_int),
            ('rhome', c_char_p),
            ('home', c_char_p),
            ('ReadConsole', c_void_p),
            ('WriteConsole', c_void_p),
            ('CallBack', c_void_p),
            ('ShowMessage', c_void_p),
            ('YesNoCancel', c_void_p),
            ('Busy', c_void_p),
            ('CharacterMode', c_int),
            ('WriteConsoleEx', c_void_p)
        ]


class Rinstance(object):
    libR = None
    _offset = None
    read_console = None
    write_console_ex = None
    polled_events = None
    clean_up = None

    def __init__(self):
        if 'R_HOME' not in os.environ:
            Rhome = subprocess.check_output(["R", "RHOME"]).decode("utf-8").strip()
            os.environ['R_HOME'] = Rhome
        else:
            Rhome = os.environ['R_HOME']
        os.environ["R_DOC_DIR"] = os.path.join(Rhome, "doc")
        os.environ["R_INCLUDE_DIR"] = os.path.join(Rhome, "include")
        os.environ["R_SHARE_DIR"] = os.path.join(Rhome, "share")
        if sys.platform.startswith("win"):
            libR_path = os.path.join(Rhome, "bin", ['i386', 'x64'][sys.maxsize > 2**32], "R.dll")
        elif sys.platform == "darwin":
            libR_path = os.path.join(Rhome, "lib", "libR.dylib")
        elif sys.platform.startswith("linux"):
            libR_path = os.path.join(Rhome, "lib", "libR.so")

        if not os.path.exists(libR_path):
            raise RuntimeError("Cannot locate R share library.")

        self.libR = CDLL(libR_path)

    def run(self):

        _argv = ["rice", "--no-save", "--quiet"]
        argn = len(_argv)
        argv = (c_char_p * argn)()
        for i, a in enumerate(_argv):
            argv[i] = c_char_p(a.encode('utf-8'))

        if sys.platform.startswith("win"):
            self.libR.R_setStartTime()
            self._setup_callbacks_win32()
            self.libR.R_set_command_line_arguments(argn, argv)
            FlushConsoleInputBuffer(GetStdHandle(STD_INPUT_HANDLE))
            self.libR.setup_term_ui()
        else:
            self.libR.Rf_initialize_R(argn, argv)
            self._setup_callbacks_unix()

        self.libR.Rf_mainloop()

    @property
    def offset(self):
        if not self._offset:
            s = ccall("Rf_ScalarInteger", self.libR, c_void_p, [c_int], 0)
            self._offset = ccall("INTEGER", self.libR, c_void_p, [c_void_p], s).value - s.value

        return self._offset

    def process_event(self):
        pass

    def ask_yes_no_cancel(self, string):
        raise "not yet implemented"

    def _setup_callbacks_win32(self):
        rstart = RStart()
        self.libR.R_DefParams(pointer(rstart))
        rstart.R_Quiet = 1
        rstart.R_Interactive = 1
        rstart.CharacterMode = 1

        rstart.rhome = ccall("get_R_HOME", self.libR, c_char_p, [])
        rstart.home = ccall("getRUser", self.libR, c_char_p, [])

        rstart.ReadConsole = cast(
            CFUNCTYPE(c_int, c_char_p, POINTER(c_char), c_int, c_int)(self.read_console),
            c_void_p)
        rstart.WriteConsole = None
        rstart.WriteConsoleEx = cast(
            CFUNCTYPE(None, c_char_p, c_int, c_int)(self.write_console_ex),
            c_void_p)
        rstart.CallBack = cast(CFUNCTYPE(None)(self.process_event), c_void_p)
        rstart.ShowMessage = cglobal("R_ShowMessage", self.libR)
        rstart.YesNoCancel = cast(CFUNCTYPE(c_char_p)(self.ask_yes_no_cancel), c_void_p)
        rstart.Busy = cglobal("R_Busy", self.libR).value

        self.libR.R_SetParams(pointer(rstart))
        self.rstart = rstart

    def _setup_callbacks_unix(self):
        if self.read_console:
            # make sure it is not gc'ed
            self.ptr_read_console = \
                CFUNCTYPE(c_int, c_char_p, POINTER(c_char), c_int, c_int)(self.read_console)
            ptr = c_void_p.in_dll(self.libR, 'ptr_R_ReadConsole')
            ptr.value = cast(self.ptr_read_console, c_void_p).value

        if self.write_console_ex:
            c_void_p.in_dll(self.libR, 'ptr_R_WriteConsole').value = 0
            # make sure it is not gc'ed
            self.ptr_write_console_ex = \
                CFUNCTYPE(None, c_char_p, c_int, c_int)(self.write_console_ex)
            ptr = c_void_p.in_dll(self.libR, 'ptr_R_WriteConsoleEx')
            ptr.value = cast(self.ptr_write_console_ex, c_void_p).value

        if self.polled_events:
            self.ptr_polled_events = CFUNCTYPE(None)(self.polled_events)
            ptr = c_void_p.in_dll(self.libR, 'R_PolledEvents')
            ptr.value = cast(self.ptr_polled_events, c_void_p).value

        if self.clean_up:
            R_CleanUp_Type = CFUNCTYPE(None, c_int, c_int, c_int)
            R_CleanUP = cglobal('ptr_R_CleanUp', self.libR, R_CleanUp_Type)

            def _handler(save_type, status, runlast):
                self.clean_up(save_type, status, runlast)
                R_CleanUP(save_type, status, runlast)

            self.ptr_r_clean_up = R_CleanUp_Type(_handler)
            ptr.value = cast(self.ptr_r_clean_up, c_void_p).value
