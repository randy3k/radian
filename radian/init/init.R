getOption("rchitect.py_tools")$attach()
radian <- import("radian")
rchitect <- import("rchitect")

register_read_console <- function(func) {
    invisible(radian$console$set_user_read_console(func))
}

unregister_read_console <- function() {
    invisible(radian$console$unset_user_read_console())
}

flush_console <- function() {
    invisible(rchitect$console$flush())
}

assign(
    ".radian.register_read_console",
    register_read_console,
    envir = .GlobalEnv)


assign(
    ".radian.unregister_read_console",
    unregister_read_console,
    envir = .GlobalEnv)


assign(
    ".radian.flush_console",
    flush_console,
    envir = .GlobalEnv)
