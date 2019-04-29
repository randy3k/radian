getOption("rchitect.py_tools")$attach()

radian <- import("radian")

keymap <- getOption("radian.escape_key_map")
if (!is.null(keymap)) {
    for (map in keymap) {
        key <- list("escape", map$key)
        value <- map$value
        mode <- if (is.null(map$mode)) "r" else map$mode
        radian$key_bindings$map_key(key, value, mode)
    }
}
