from __future__ import unicode_literals
import sys
import re
import ctypes


if sys.platform == "win32":
    wctomb = ctypes.cdll.msvcrt.wctomb
    wctomb.argtypes = [ctypes.POINTER(ctypes.c_char), ctypes.c_wchar]
    wctomb.restype = ctypes.c_int

    mbtowc = ctypes.cdll.msvcrt.mbtowc
    mbtowc.argtypes = [ctypes.POINTER(ctypes.c_wchar), ctypes.POINTER(ctypes.c_char), ctypes.c_size_t]
    mbtowc.restype = ctypes.c_int


UTFPATTERN = re.compile(b"\x02\xff\xfe(.*?)\x03\xff\xfe")


def rconsole2str(buf):
    ret = ""
    m = UTFPATTERN.search(buf)
    while m:
        a, b = m.span()
        ret += system2utf8(buf[:a]) + m.group(1).decode("utf-8", "backslashreplace")
        buf = buf[b:]
        m = UTFPATTERN.search(buf)
    ret += system2utf8(buf)
    return ret


if sys.version >= "3":
    def ask_input(s):
        return input(s)
else:
    def ask_input(s):
        return raw_input(s).decode("utf-8", "backslashreplace")


if sys.platform == "win32":

    def system2utf8(buf):
        wcbuf = ctypes.create_unicode_buffer(1)
        text = ""
        while buf:
            n = mbtowc(wcbuf, buf, len(buf))
            if n <= 0:
                break
            text += wcbuf[0]
            buf = buf[n:]
        return text

    def utf8tosystem(text):
        s = ctypes.create_string_buffer(10)
        buf = b""
        for c in text:
            n = wctomb(s, c)
            if n > 0:
                buf += s[:n]
            else:
                buf += "\\u{{{}}}".format(hex(ord(c))[2:]).encode("ascii")
        return buf

else:
    def system2utf8(buf):
        return buf.decode("utf-8", "backslashreplace")

    def utf8tosystem(text):
        return text.encode("utf-8", "backslashreplace")


def create_read_console(get_text):
    code = [None]

    def _read_console(p, buf, buflen, add_history):
        if not code[0]:
            text = get_text(rconsole2str(p), add_history)
            if text is None:
                return 0
            code[0] = utf8tosystem(text)

        nb = min(len(code[0]), buflen - 2)
        for i in range(nb):
            buf[i] = code[0][i]
        if nb < buflen - 2:
            buf[nb] = b'\n'
            buf[nb + 1] = b'\0'
        code[0] = code[0][nb:]
        return 1

    return _read_console


def write_console_ex(buf, buflen, otype):
    buf = rconsole2str(buf)
    if otype == 0:
        sys.stdout.write(buf)
        sys.stdout.flush()
    else:
        if sys.stderr:
            sys.stderr.write(buf)
            sys.stderr.flush()
    pass


def busy(which):
    pass


def clean_up(save_type, status, runlast):
    pass


def polled_events():
    pass


def show_message(buf):
    buf = rconsole2str(buf)
    sys.stdout.write(buf)
    sys.stdout.flush()


def ask_yes_no_cancel(p):
    while True:
        try:
            result = ask_input("{} [y/n/c]: ".format(rconsole2str(p)))
            if result in ["Y", "y"]:
                return 1
            elif result in ["N", "n"]:
                return 2
            else:
                return 0
        except EOFError:
            return 0
        except KeyboardInterrupt:
            return 0
        except Exception:
            pass
