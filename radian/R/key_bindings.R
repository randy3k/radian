getOption("rchitect.py_tools")$attach()

radian <- import("radian")

esc_keymap <- getOption("radian.escape_key_map")
if (!is.null(esc_keymap)) {
    for (map in esc_keymap) {
        key <- list("escape", map$key)
        value <- map$value
        mode <- if (is.null(map$mode)) "r" else map$mode
        radian$key_bindings$map_key(key, value, mode)
    }
}


# not documented
keymap <- getOption("radian.key_map")
if (!is.null(keymap)) {
    for (map in keymap) {
        key <- as.list(map$key)
        value <- map$value
        mode <- if (is.null(map$mode)) "r" else map$mode
        radian$key_bindings$map_key(key, value, mode)
    }
}
