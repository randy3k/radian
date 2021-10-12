from rchitect.interface import dispatch
from prompt_toolkit.keys import Keys


@dispatch(Keys)
def sexpclass(s): # noqa
    return "PyObject"
