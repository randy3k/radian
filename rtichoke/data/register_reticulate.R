# register reticulate prompt

local({
    rtichoke <- .py::py_import("rtichoke")
    builtin <- .py::py_import("builtins")
    prompt_toolkit <- .py::py_import("prompt_toolkit")
    pygments <- .py::py_import("pygments")
    .py::py_import("pygments.lexers.python")
    operator <- .py::py_import("operator")

    PygmentsLexer <- prompt_toolkit$lexers$PygmentsLexer
    app <- rtichoke$get_app()
    app$session$register_mode(
        "reticulate",
        native = TRUE,
        activator = function(session) reticulate:::.globals$py_repl_active,
        message = function() app$session$prompt_text,
        insert_new_line = FALSE,
        lexer = PygmentsLexer(pygments$lexers$python$PythonLexer)
    )
    invisible(NULL)
})
