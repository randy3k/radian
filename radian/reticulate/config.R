getOption("rchitect.py_tools")$attach()
ns <- getNamespace("reticulate")

rchitect <- import("rchitect")
radian <- import("radian")
sys <- import("sys")
os <- import("os")

unlockBinding("initialize_python", ns)

old_initialize_python <- ns$initialize_python

discover_radian <- function(python) {
    res <- suppressWarnings(system2(
        python, shQuote(c("-c", "import radian; print(radian.__version__)")),
        stdout = TRUE, stderr = TRUE))
    if (!(is.null(attr(res, "status"))) && attr(res, "status") != 0) {
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


normalize_version <- function(v) {
    tags <- strsplit(v, "\\.")[[1]]
    if (length(tags) == 4) {
        m <- as.integer(tags[1:3])
        if (m[3] != 0) {
            m[3] <- m[3] - 1
        } else if (m[2] != 0) {
            m[2] <- m[2] - 1
            m[3] <- 9999
        } else {
            m[1] <- m[1] - 1
            m[2:3] <- 9999
        }
        paste0(m[1:3], collapse = ".")
    } else {
        paste0(tags[1:3], collapse = ".")
    }
}


compare_version <- function(a, b) {
    utils::compareVersion(normalize_version(a), normalize_version(b))
}

assign(
    "initialize_python",
    function(required_module = NULL, use_environment = NULL, ...) {
        "patched by radian"
        config <- reticulate::py_discover_config(required_module, use_environment)
        sys_python <- reticulate:::canonical_path(sys$executable)
        if (config$python != sys_python) {
            if (isTRUE(getOption("radian.force_reticulate_python", FALSE))) {
                ans <- FALSE
            } else {
                message("Python version used by reticulate is ",
                    "different to the current python runtime")
                message("current: ", sys_python)
                message("target: ", config$python)
                message("Switch to radian in target python environment? ")
                ans <- utils::askYesNo("The current workspace will be lost. Confirm?")
            }

            if (is.na(ans)) {
                stop("action aborted", call. = FALSE)
            } else if (isTRUE(ans)) {
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

                args <- sys$argv[-1]
                if (.Platform$OS.type == "windows") {
                    is_powershell <- length(strsplit(Sys.getenv("PSModulePath"), ";")[[1]]) >= 3

                    # os.execv doesn't work well on windows
                    # so we just instruct user how to open the other radian
                    cmd <- paste(c(shQuote(config$python), "-m", "radian", args), collapse = " ")
                    if (is_powershell) {
                        cmd <- paste("&", cmd)
                    }
                    utils::writeClipboard(cmd)
                    message("the target radian cannot be launched automatically")
                    message("please run the following command manually (copied to clipboard)")
                    message(cmd)
                    quit(save = "no")
                } else {
                    message("radian: switch to v", target_ver, " at ", config$python)
                    os$execv(config$python, c(config$python, "-m", "radian", args))
                }
            } else {
                message("radian: force reticulate to use ", sys_python)
            }
        }
        rchitect$reticulate$configure()
        old_initialize_python(
            required_module = required_module, use_environment = use_environment, ...)
    },
    ns)

lockBinding("initialize_python", ns)
