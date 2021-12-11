getOption("rchitect.py_tools")$attach()
radian <- import("radian")

register_read_console <- function(func) {
    invisible(radian$console$set_user_read_console(func))
}

assign(
    ".radian.register_read_console",
    register_read_console,
    envir = .GlobalEnv)
