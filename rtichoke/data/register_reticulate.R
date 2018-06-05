# register reticulate prompt

local({
    rtichoke <- .py::py_import("rtichoke")
    prompt_toolkit <- .py::py_import("prompt_toolkit")
    pygments <- .py::py_import("pygments")
    .py::py_import("pygments.lexers.python")
    operator <- .py::py_import("operator")
    builtins <- .py::py_import("builtins")

    PygmentsLexer <- prompt_toolkit$lexers$PygmentsLexer
    KeyBindings <- prompt_toolkit$key_binding$key_bindings$KeyBindings

    `|.PyObject` <- function(x, y) .py::py_call(operator$or_, x, y)
    `&.PyObject` <- function(x, y) .py::py_call(operator$and_, x, y)

    emacs_insert_mode <- prompt_toolkit$filters$emacs_insert_mode
    vi_insert_mode <- prompt_toolkit$filters$vi_insert_mode
    insert_mode <- vi_insert_mode | emacs_insert_mode
    default_focussed <- rtichoke$keybindings$default_focussed

    prase_text_complete <- function(text) {
        if (grepl("\n", text)) {
            return(!is.null(tryCatch(
                builtins$compile(text, "<input>", "exec"),
                error = function(e) NULL
            )))
        } else {
            return(!is.null(tryCatch(
                builtins$compile(text, "<input>", "single"),
                error = function(e) NULL
            )))
        }
    }

    kb <- KeyBindings()
    rtichoke$keybindings$add_prompt_keybindings(kb, prase_text_complete)

    codeenv <- new.env()

    handle_code <- function(code) {
        # import builtins from reticulate rather than .py because we need globals and locals
        builtins <- reticulate::import_builtins(convert = FALSE)
        if (grepl("\n", code)) {
            # reticulate repl doesn't handle multiline code, we have to execuate it manually
            codeenv$evaluated <- TRUE
            locals <- reticulate::py_run_string("locals()")
            globals <- reticulate::py_run_string("globals()")
            output <- tryCatch(
                builtins$eval(builtins$compile(code, "<input>", "exec"), locals, globals),
                error = function(e) e)
            if (inherits(output, "error")) {
                error <- reticulate::py_last_error()
                message(paste(error$type, error$value, sep = ": "))
            }
        } else {
            codeenv$evaluated <- FALSE
        }
        code
    }

    app <- rtichoke$get_app()
    app$session$register_mode(
        "reticulate",
        native = FALSE,
        on_done = function(session) handle_code(.py::py_copy(session$default_buffer$text)),
        return_result = function(result) !codeenv$evaluated,
        activator = function(session) reticulate:::py_repl_active(),
        message = function() app$session$prompt_text,
        multiline = TRUE,
        insert_new_line = TRUE,
        lexer = PygmentsLexer(pygments$lexers$python$PythonLexer),
        prompt_key_bindings = kb
    )
    invisible(NULL)
})
