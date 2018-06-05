# register reticulate prompt

rtichoke <- .py::import("rtichoke")
prompt_toolkit <- .py::import("prompt_toolkit")
pygments <- .py::import("pygments")
operator <- .py::import("operator")
sys <- .py::import("sys")
builtins <- .py::import_builtins()

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
        if (xor(substr(text, 1, 1) == "?", substr(text, nchar(text), nchar(text)) == "?")) {
            return(TRUE)
        } else {
            return(!is.null(tryCatch(
                builtins$compile(text, "<input>", "single"),
                error = function(e) NULL
            )))
        }
    }
}

kb <- rtichoke$keybindings$create_prompt_keybindings(prase_text_complete)

codeenv <- new.env()

handle_code <- function(code) {
    code <- trimws(code, which = "right")
    if (grepl("\n", code)) {
        # reticulate repl doesn't handle multiline code, we have to execuate it manually
        handle_multiline_code(code)
        codeenv$evaluated <- TRUE
    } else {
        codeenv$evaluated <- FALSE
    }
    code
}

leading_spaces <- function(x) regmatches(x, regexpr("^\\s*", x))

handle_multiline_code <- function(code) {
    # import builtins from reticulate rather than .py because we need globals and locals
    builtins <- reticulate::import_builtins(convert = FALSE)
    locals <- reticulate::py_run_string("locals()")
    globals <- reticulate::py_run_string("globals()")
    lines <- gsub("\r", "", strsplit(code, "\n")[[1]])

    # try spliting the last line
    firstline <- trimws(lines[[1]], which = "right")
    lastline <- lines[[length(lines)]]
    complied <- tryCatch(
        builtins$compile(paste(lines[-length(lines)], collapse = "\n"), "<input>", "exec"),
        error = function(e) e)
    if ((!inherits(complied, "error")) &&
                (leading_spaces(firstline) == leading_spaces(lastline))) {
        output <- tryCatch({
            builtins$eval(complied, locals, globals)
            builtins$eval(builtins$compile(lastline, "<input>", "single"), locals, globals)
            },
            error = function(e) e)
    } else {
        output <- tryCatch(
            builtins$eval(builtins$compile(code, "<input>", "exec"), locals, globals),
            error = function(e) e)
    }
    if (inherits(output, "error")) {
        error <- reticulate::py_last_error()
        message(paste(error$type, error$value, sep = ": "))
    }
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
