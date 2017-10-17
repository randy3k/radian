from __future__ import unicode_literals
import os
import subprocess
import sys
import ctypes
from ctypes import c_char, c_char_p, c_int, c_size_t, c_void_p, \
    cast, pointer, PyDLL, CFUNCTYPE, POINTER
from .util import ccall, read_registry


if sys.platform.startswith("win"):
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
            ('rhome', POINTER(c_char)),
            ('home', POINTER(c_char)),
            ('ReadConsole', c_void_p),
            ('WriteConsole', c_void_p),
            ('CallBack', c_void_p),
            ('ShowMessage', c_void_p),
            ('YesNoCancel', c_void_p),
            ('Busy', c_void_p),
            ('CharacterMode', c_int),
            ('WriteConsoleEx', c_void_p)
        ]


class RSession(object):
    libR = None
    _offset = None
    read_console = None
    write_console_ex = None
    process_event = None
    show_message = None
    clean_up = None

    def __init__(self):
        if 'R_HOME' not in os.environ:
            try:
                Rhome = subprocess.check_output(["R", "RHOME"]).decode("utf-8").strip()
            except FileNotFoundError as e:
                if sys.platform.startswith("win"):
                    Rexe = os.path.join(
                        read_registry("Software\\R-Core\\R", "InstallPath")[0],
                        "bin",
                        "R.exe")
                    Rhome = subprocess.check_output([Rexe, "RHOME"]).decode("utf-8").strip()
                else:
                    raise e

            os.environ['R_HOME'] = Rhome
        else:
            Rhome = os.environ['R_HOME']
        os.environ["R_DOC_DIR"] = os.path.join(Rhome, "doc")
        os.environ["R_INCLUDE_DIR"] = os.path.join(Rhome, "include")
        os.environ["R_SHARE_DIR"] = os.path.join(Rhome, "share")

        if sys.platform.startswith("win"):
            libR_dir = os.path.join(Rhome, "bin", ['i386', 'x64'][sys.maxsize > 2**32])
            os.environ['PATH'] = os.environ['PATH'] + ";" + libR_dir

            libR_path = os.path.join(libR_dir, "R.dll")
        elif sys.platform == "darwin":
            libR_path = os.path.join(Rhome, "lib", "libR.dylib")
        elif sys.platform.startswith("linux"):
            libR_path = os.path.join(Rhome, "lib", "libR.so")

        if not os.path.exists(libR_path):
            raise RuntimeError("Cannot locate R share library.")

        self.libR = PyDLL(str(libR_path))

    def run(self):

        _argv = ["rice", "--no-save", "--no-restore-data", "--quiet"]
        argn = len(_argv)
        argv = (c_char_p * argn)()
        for i, a in enumerate(_argv):
            argv[i] = c_char_p(a.encode('utf-8'))

        if sys.platform.startswith("win"):
            self.libR.R_setStartTime()
            self.setup_callbacks_win32()
            self.libR.R_set_command_line_arguments(argn, argv)
        else:
            self.libR.Rf_initialize_R(argn, argv)
            self.setup_callbacks_posix()

        self.libR.Rf_mainloop()

    @property
    def offset(self):
        if not self._offset:
            s = ccall("Rf_ScalarInteger", self.libR, c_void_p, [c_int], 0)
            self._offset = ccall("INTEGER", self.libR, c_void_p, [c_void_p], s).value - s.value

        return self._offset

    def polled_events(self):
        pass

    def ask_yes_no_cancel(self, string):
        raise "not yet implemented"

    def r_busy(self, which):
        pass

    def setup_callbacks_win32(self):
        rstart = RStart()
        self.libR.R_DefParams(pointer(rstart))

        rstart.rhome = ccall("get_R_HOME", self.libR, POINTER(c_char), [])
        rstart.home = ccall("getRUser", self.libR, POINTER(c_char), [])
        rstart.CharacterMode = 0
        rstart.ReadConsole = cast(
            CFUNCTYPE(c_int, c_char_p, POINTER(c_char), c_int, c_int)(self.read_console),
            c_void_p)
        rstart.WriteConsole = None
        rstart.WriteConsoleEx = cast(
            CFUNCTYPE(None, c_char_p, c_int, c_int)(self.write_console_ex),
            c_void_p)
        rstart.CallBack = cast(CFUNCTYPE(None)(self.polled_events), c_void_p)
        rstart.ShowMessage = cast(CFUNCTYPE(None, c_char_p)(self.show_message), c_void_p)
        rstart.YesNoCancel = cast(CFUNCTYPE(c_int, c_char_p)(self.ask_yes_no_cancel), c_void_p)
        rstart.Busy = cast(CFUNCTYPE(None, c_int)(self.r_busy), c_void_p)

        rstart.R_Quiet = 1
        rstart.R_Interactive = 1
        rstart.RestoreAction = 0
        rstart.SaveAction = 0

        self.libR.R_SetParams(pointer(rstart))

        self.rstart = rstart

    def setup_callbacks_posix(self):

        # ptr_R_Suicide

        if self.show_message:
            self.ptr_show_message = CFUNCTYPE(None, c_char_p)(self.show_message)
            ptr = c_void_p.in_dll(self.libR, 'ptr_R_ShowMessage')
            ptr.value = cast(self.ptr_show_message, c_void_p).value

        if self.read_console:
            # make sure it is not gc'ed
            self.ptr_read_console = \
                CFUNCTYPE(c_int, c_char_p, POINTER(c_char), c_int, c_int)(self.read_console)
            ptr = c_void_p.in_dll(self.libR, 'ptr_R_ReadConsole')
            ptr.value = cast(self.ptr_read_console, c_void_p).value

        if self.write_console_ex:
            c_void_p.in_dll(self.libR, 'ptr_R_WriteConsole').value = None
            # make sure it is not gc'ed
            self.ptr_write_console_ex = \
                CFUNCTYPE(None, c_char_p, c_int, c_int)(self.write_console_ex)
            ptr = c_void_p.in_dll(self.libR, 'ptr_R_WriteConsoleEx')
            ptr.value = cast(self.ptr_write_console_ex, c_void_p).value

        # ptr_R_ResetConsole
        # ptr_R_FlushConsole
        # ptr_R_ClearerrConsole

        if self.r_busy:
            self.ptr_r_busy = CFUNCTYPE(None, c_int)(self.r_busy)
            ptr = c_void_p.in_dll(self.libR, 'ptr_R_Busy')
            ptr.value = cast(self.ptr_r_busy, c_void_p).value

        if self.clean_up:
            ptr = c_void_p.in_dll(self.libR, 'ptr_R_CleanUp')
            R_CleanUp = CFUNCTYPE(None, c_int, c_int, c_int)(ptr.value)

            def _handler(save_type, status, runlast):
                self.clean_up(save_type, status, runlast)
                R_CleanUp(save_type, status, runlast)

            self.ptr_r_clean_up = CFUNCTYPE(None, c_int, c_int, c_int)(_handler)
            ptr.value = cast(self.ptr_r_clean_up, c_void_p).value

        # ptr_R_ShowFiles
        # ptr_R_ChooseFile
        # ptr_R_EditFile
        # ptr_R_loadhistory
        # ptr_R_savehistory
        # ptr_R_addhistory
        # ptr_R_EditFiles
        # ptr_do_selectlist
        # ptr_do_dataentry
        # ptr_do_dataviewer

        if self.process_event:
            self.ptr_process_event = CFUNCTYPE(None)(self.process_event)
            ptr = c_void_p.in_dll(self.libR, 'ptr_R_ProcessEvents')
            ptr.value = cast(self.ptr_process_event, c_void_p).value

        if self.polled_events:
            self.ptr_polled_events = CFUNCTYPE(None)(self.polled_events)
            ptr = c_void_p.in_dll(self.libR, 'R_PolledEvents')
            ptr.value = cast(self.ptr_polled_events, c_void_p).value
