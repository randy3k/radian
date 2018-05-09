from __future__ import unicode_literals
import ctypes
import sys
import re
import rapi


def encoding():
    if sys.platform == "win32":
        cp = rapi.utils.cglobal("localeCP", rapi.libR, ctypes.c_int)
        if cp and cp.value:
            return "cp" + str(cp.value)

    return "utf-8"


UTFPATTERN = re.compile(b"\x02\xff\xfe(.*?)\x03\xff\xfe")


def create_read_console(get_text):
    code = [None]

    def _read_console(p, buf, buflen, add_history):
        if not code[0]:
            text = get_text(p.decode(encoding()), add_history)
            if text is None:
                return 0
            code[0] = text.encode(encoding())

        addr = ctypes.addressof(buf.contents)
        c2 = (ctypes.c_char * buflen).from_address(addr)
        nb = min(len(code[0]), buflen - 2)
        c2[:nb] = code[0][:nb]
        if nb < buflen - 2:
            c2[nb:(nb + 2)] = b'\n\0'
        code[0] = code[0][nb:]
        return 1

    return _read_console


def rconsole2str(buf, encoding):
    ret = ""
    m = UTFPATTERN.search(buf)
    while m:
        a, b = m.span()
        ret += buf[:a].decode(encoding) + m.group(1).decode("utf-8")
        buf = buf[b:]
        m = UTFPATTERN.search(buf)
    ret += buf.decode(encoding)
    return ret


def write_console_ex(buf, buflen, otype):
    buf = rconsole2str(buf, encoding())
    if otype == 0:
        sys.stdout.write(buf)
        sys.stdout.flush()
    else:
        if sys.stderr:
            sys.stderr.write(buf)
            sys.stderr.flush()
    pass


def clean_up(save_type, status, runlast):
    pass


def show_message(buf):
    buf = rconsole2str(buf, encoding())
    sys.stdout.write(buf)
    sys.stdout.flush()


def ask_yes_no_cancel(string):
    while True:
        try:
            result = str(input("{} [y/n/c]: ".format(string.decode(encoding()))))
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
