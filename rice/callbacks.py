from __future__ import unicode_literals
import ctypes
import sys

# to be set by RiceApplication
ENCODING = "utf-8"


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


def write_console_ex(buf, buflen, otype):
    try:
        output = buf.decode(ENCODING)
        if otype == 0:
            sys.stdout.write(output)
            sys.stdout.flush()
        else:
            sys.stderr.write(output)
            sys.stderr.flush()
    except UnicodeEncodeError as e:
        # catch print error when terminal doesn't support unicode
        pass


def clean_up(save_type, status, runlast):
    pass


def show_message(buf):
    sys.stdout.write(buf.decode(ENCODING))
    sys.stdout.flush()
