from __future__ import unicode_literals
from collections import OrderedDict
from . import api
from ctypes import c_int

import os
import time
from six import text_type

"""
High level functions to interact with R api.
"""


def prase_input_complete(s):
    status = c_int()
    api.safe_parse_vector(api.mk_string(s), status)
    return status.value != 2


def rcopy(s, simplify=False):
    api.protect(s)
    ret = None
    typ = api.typeof(s)
    if typ == api.VECSXP:
        ret = OrderedDict()
        names = rcopy(rcall(api.mk_symbol("names"), s))
        for i in range(api.length(s)):
            ret[names[i]] = rcopy(api.vector_elt(s, i), simplify=simplify)
    elif typ == api.STRSXP:
        enc = api.encoding()
        ret = []
        for i in range(api.length(s)):
            ret.append(api.dataptr(api.string_elt(s, i)).value.decode(enc))
        if simplify and len(ret) == 1:
            ret = ret[0]
    elif typ == api.LGLSXP:
        ret = []
        sp = api.dataptr(s)
        for i in range(api.length(s)):
            ret.append(bool(sp[i]))
        if simplify and len(ret) == 1:
            ret = ret[0]
    elif typ == api.INTSXP:
        ret = []
        sp = api.dataptr(s)
        for i in range(api.length(s)):
            ret.append(int(sp[i]))
        if simplify and len(ret) == 1:
            ret = ret[0]
    elif typ == api.REALSXP:
        ret = []
        sp = api.dataptr(s)
        for i in range(api.length(s)):
            ret.append(sp[i])
        if simplify and len(ret) == 1:
            ret = ret[0]
    api.unprotect(1)
    return ret


def rlang(*args, **kwargs):
    nargs = len(args) + len(kwargs)
    t = api.protect(api.alloc_vector(api.LANGSXP, nargs))
    s = t
    api.setcar(s, args[0])
    for a in args[1:]:
        s = api.cdr(s)
        api.setcar(s, a)
    for k, v in kwargs.items():
        s = api.cdr(s)
        api.setcar(s, v)
        api.settag(s, api.mk_symbol(k))
    api.unprotect(1)
    return t


def rcall(*args, **kwargs):
    status = c_int()
    val = api.try_eval(rlang(*args, **kwargs), status=status)
    if status.value != 0:
        raise RuntimeError("R eval error.")
    return val


def rparse(s):
    status = c_int()
    val = api.parse_vector(api.mk_string(s), status)
    if status.value != 1:
        raise SyntaxError("Error: %s" % api.parse_error_msg())
    return val


def reval(s):
    try:
        exprs = rparse(s)
    except Exception as e:
        raise e
    api.protect(exprs)
    status = c_int()
    val = None
    try:
        for i in range(0, api.length(exprs)):
            val = api.try_eval(api.vector_elt(exprs, i), status)
            if status.value != 0:
                raise RuntimeError("R eval error.")
    finally:
        api.unprotect(1)  # exprs
    return val


def rprint(s):
    api.protect(s)
    try:
        rcall(api.mk_symbol("print"), s)
    finally:
        api.unprotect(1)


def get_option(key, default=None):
    ret = rcopy(api.get_option1(api.mk_symbol(key)), simplify=True)
    if ret is None:
        return default
    else:
        return ret


def set_option(key, value):
    kwargs = {}
    if isinstance(value, text_type):
        kwargs[key] = api.mk_string(value)
    elif isinstance(value, bool):
        kwargs[key] = api.scalar_integer(int(value))
    elif isinstance(value, int):
        kwargs[key] = api.scalar_integer(value)

    rcall(api.mk_symbol("options"), **kwargs)


def r_version():
    info = rcopy(rcall(api.mk_symbol("R.Version")), simplify=True)
    return "{} -- {}\nPlatform: {}\n".format(
        info["version.string"], info["nickname"], info["platform"])


def make_installed_packages():
    last_time = [0]
    _packages = [None]

    def f():
        if time.time() - last_time[0] > 5:
            paths = rcopy(reval("base::.libPaths()"))
            _packages[0] = []

            for path in paths:
                _packages[0] = _packages[0] + \
                    [d for d in os.listdir(path)
                        if os.path.exists(os.path.join(path, d, "DESCRIPTION"))]
        return _packages[0]
    return f


installed_packages = make_installed_packages()


def reticulate_set_message(message):
    reval("""
    setHook(packageEvent("reticulate", "onLoad"),
            function(...) packageStartupMessage("{}"))
    """.format(message.replace('\\', '\\\\').replace('"', '\\"')))
