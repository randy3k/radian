rchitect <- getOption("rchitect_environment")
import <- rchitect$import
import_builtins <- rchitect$import_builtins
py_call <- rchitect$py_call
py_eval <- rchitect$py_eval
py_copy <- rchitect$py_copy
tuple <- rchitect$tuple
dict <- rchitect$dict
`$.PyObject` <- rchitect$`$.PyObject`
`[.PyObject` <- rchitect$`[.PyObject`

py_config <- import("radian.py_config")
native_config <- py_copy(py_config$config())

reticulate_ns <- getNamespace("reticulate")

unlockBinding("py_discover_config", reticulate_ns)

old_py_discover_config <- reticulate_ns$py_discover_config

assign(
    "py_discover_config",
    function(...) {
        config <- old_py_discover_config(...)
        config$python <- native_config[[1]]
        config$libpython <- native_config[[2]]
        config
    },
    reticulate_ns)

lockBinding("py_discover_config", reticulate_ns)
