getOption("rchitect.py_tools")$attach()
ns <- getNamespace("reticulate")

rchitect <- import("rchitect")
sys <- import("sys")
os <- import("os")
radian <- import("radian")

unlockBinding("initialize_python", ns)

old_initialize_python <- ns$initialize_python

discover_radian <- function(python) {
    res <- suppressWarnings(system2(
        python, shQuote(c("-c", "import radian; print(radian.__version__)")),
        stdout = TRUE, stderr = TRUE))
    if (!(is.null(attr(res, "status"))) && attr(res, "status") == 0) {
        NULL
    } else {
        res
    }
}

offer_install_radian <- function(python) {
    message("radian was not installed in the target")
    ans2 <- utils::askYesNo("Install it via pip?")
    if (!isTRUE(ans2)) {
        stop("action aborted", call. = FALSE)
    }
    system2(python, c("-m", "pip", "install", "radian"))
    discover_radian(python)
}

offer_upgrade_radian <- function(python, target_ver, current_ver) {
    message("radian in target (v", target_ver, ")",
        " is older than the current version (v", current_ver, ")")
    ans2 <- utils::askYesNo("Upgrade it via pip?")
    if (isTRUE(ans2)) {
        system2(python, c("-m", "pip", "install", "-U", "radian"))
    }
    discover_radian(python)
}

compare_version <- function(a, b) {
    a <- paste0(strsplit(a, "\\.")[[1]][1:3], collapse = ".")
    b <- paste0(strsplit(b, "\\.")[[1]][1:3], collapse = ".")
    utils::compareVersion(a, b)
}

assign(
    "initialize_python",
    function(required_module = NULL, use_environment = NULL, ...) {
        "patched by radian"
        config <- reticulate::py_discover_config(required_module, use_environment)
        sys_python <- reticulate:::canonical_path(sys$executable)
        if (config$python != sys_python) {
            message("radian: Python version used by reticulate is ",
                "different to the current python runtime")
            message("current: ", sys_python)
            message("target: ", config$python)
            ans <- utils::askYesNo("Do you want to switch to radian in target python environment?")

            if (is.na(ans)) {
                stop("action aborted", call. = FALSE)
            } else if (isTRUE(ans)) {
                args <- c(sys$argv[-1], "--quiet")
                target_ver <- discover_radian(config$python)
                current_ver <- radian$`__version__`
                if (is.null(target_ver)) {
                    target_ver <- offer_install_radian(config$python)
                } else if (compare_version(current_ver, target_ver) > 0) {
                    target_ver <- offer_upgrade_radian(config$python, target_ver, current_ver)
                }

                if (is.null(target_ver)) {
                    stop("error in installing radian in the target")
                }
                message("radian: switch to v", target_ver, " at ", config$python)
                os$execv(config$python, c(config$python, "-m", "radian", args))
            } else {
                message("radian: ignore python discovered by reticulate")
                message("radian: force reticulate to use ", sys_python)
            }
        }
        rchitect$reticulate$configure()
        old_initialize_python(
            required_module = required_module, use_environment = use_environment, ...)
    },
    ns)

lockBinding("initialize_python", ns)
