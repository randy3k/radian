getOption("rchitect.py_tools")$attach()
ns <- getNamespace("reticulate")

rchitect <- import("rchitect")
sys <- import("sys")

force_reticulate <- function() {
    message("radian: force reticulate to use ", sys$executable)
    Sys.setenv(RETICULATE_PYTHON = sys$executable)
}

old_initialize_python <- ns$initialize_python

if (compareVersion(as.character(packageVersion("reticulate")), "1.18.9008") == -1) {
    # new version of reticulate doesn't require this
    # https://github.com/rstudio/reticulate/pull/279

    if (isTRUE(getOption("radian.force_reticulate_python", FALSE))) {
        force_reticulate()
    }

    unlockBinding("initialize_python", ns)
    assign(
    "initialize_python",
    function(required_module = NULL, use_environment = NULL, ...) {
        "patched by radian"
        config <- reticulate::py_discover_config(required_module, use_environment)
        sys_python <- reticulate:::canonical_path(sys$executable)
        if (config$python != sys_python) {
            message("Python version used by reticulate is ",
                "different to the current python runtime")
            message("current: ", sys_python)
            message("reticulate: ", config$python)
            force_reticulate()
        }
        rchitect$reticulate$configure()
        old_initialize_python(
            required_module = required_module, use_environment = use_environment, ...)
    },
    ns)

    lockBinding("initialize_python", ns)
} else {
    rchitect$reticulate$configure()
}
