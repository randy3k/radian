from __future__ import unicode_literals
import sys
import re


if sys.platform == "win32":
    ENCODING = "latin-1"
else:
    ENCODING = "utf-8"

UTFPATTERN = re.compile(b"\x02\xff\xfe(.*?)\x03\xff\xfe")


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


def set_encoding(enc):
    global ENCODING
    ENCODING = enc


def create_read_console(get_text):
    code = [None]

    def _read_console(p, buf, buflen, add_history):
        if not code[0]:
            text = get_text(p.decode(ENCODING), add_history)
            if text is None:
                return 0
            code[0] = text.encode(ENCODING)

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
    buf = rconsole2str(buf, ENCODING)
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
