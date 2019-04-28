getOption("rchitect.py_tools")$attach()

radian <- import("radian")

keymap <- getOption("radian.key_map")
if (!is.null(keymap)) {
    for (map in keymap) {
        key <- map$key
        value <- map$value
        mode <- if (is.null(map$mode)) "r" else map$mode
        radian$key_bindings$map_key(key, value, mode)
    }
}
