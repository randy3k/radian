from __future__ import unicode_literals
import ctypes
import sys
import re

# to be set by RtichokeApplication
if sys.platform.startswith("win"):
    ENCODING = "latin-1"
else:
    ENCODING = "utf-8"

UTFPATTERN = re.compile(b"\x02\xff\xfe(.*?)\x03\xff\xfe")


def create_read_console(get_text):
    code = [None]

    def _read_console(p, buf, buflen, add_history):
        if not code[0]:
            text = get_text(p.decode(ENCODING), add_history)
            if text is None:
                return 0
            code[0] = text.encode(ENCODING)

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
    buf = rconsole2str(buf, ENCODING)
    if otype == 0:
        sys.stdout.write(buf)
        sys.stdout.flush()
    else:
        sys.stderr.write(buf)
        sys.stderr.flush()
    pass


def clean_up(save_type, status, runlast):
    pass


def show_message(buf):
    buf = rconsole2str(buf, ENCODING)
    sys.stdout.write(buf)
    sys.stdout.flush()


def ask_yes_no_cancel(string):
    while True:
        try:
            result = str(input("{} [y/n/c]: ".format(string.decode(ENCODING))))
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
