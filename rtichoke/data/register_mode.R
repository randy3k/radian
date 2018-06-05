# register a custom prompt which evaluates R expressions in an sandbox environment

local({
    rtichoke <- .py::py_import("rtichoke")
    builtin <- .py::py_import("builtins")
    prompt_toolkit <- .py::py_import("prompt_toolkit")
    pygments <- .py::py_import("pygments")
    operator <- .py::py_import("operator")

    PygmentsLexer <- prompt_toolkit$lexers$PygmentsLexer
    KeyBindings <- prompt_toolkit$key_binding$key_bindings$KeyBindings

    `|.PyObject` <- function(x, y) .py::py_call(operator$or_, x, y)
    `&.PyObject` <- function(x, y) .py::py_call(operator$and_, x, y)

    emacs_insert_mode <- prompt_toolkit$filters$emacs_insert_mode
    vi_insert_mode <- prompt_toolkit$filters$vi_insert_mode
    insert_mode <- vi_insert_mode | emacs_insert_mode
    is_begin_of_buffer <- rtichoke$keybindings$is_begin_of_buffer
    default_focussed <- rtichoke$keybindings$default_focussed

    kb <- KeyBindings()
    kb$add("#", filter = insert_mode & default_focussed & is_begin_of_buffer)(
        function(event) event$app$session$change_mode("env")
    )

    pkb <- KeyBindings()
    pkb$add("backspace", filter = insert_mode & default_focussed & is_begin_of_buffer)(
        function(event) event$app$session$change_mode("r")
    )

    app <- rtichoke$get_app()
    env <- new.env()
    app$session$register_mode(
        "env",
        native = FALSE,
        message = "env> ",
        insert_new_line = TRUE,
        lexer = PygmentsLexer(pygments$lexers$r$SLexer),
        on_done = function(session) {
            text <- .py::py_copy(session$default_buffer$text)
            if (nzchar(text) > 0) {
                tryCatch({
                    result <- withVisible(eval(parse(text = text), env = env))
                    if (result$visible) {
                        print(result$value)
                    }
                },
                error = function(e) {
                    cat("error\n")
                }
                )
            }
        },
        key_bindings = kb,
        prompt_key_bindings = pkb
    )
    invisible(NULL)
})
