from __future__ import unicode_literals
import ctypes


def create_read_console(get_text):
    code = [None]

    def _read_console(p, buf, buflen, add_history):
        if not code[0]:
            text = get_text(p.decode("utf-8"))
            if text is None:
                return 0
            code[0] = text.encode("utf-8")

        addr = ctypes.addressof(buf.contents)
        c2 = (ctypes.c_char * buflen).from_address(addr)
        nb = min(len(code[0]), buflen - 2)
        c2[:nb] = code[0][:nb]
        if nb < buflen - 2:
            c2[nb:(nb + 2)] = b'\n\0'
        code[0] = code[0][nb:]
        return 1

    return _read_console


def create_write_console_ex(_handler):
    def _write_console_ex(buf, buflen, otype):

        output = buf.decode("utf-8")
        _handler(output, otype)

    return _write_console_ex
