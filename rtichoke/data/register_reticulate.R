# register reticulate prompt

rtichoke <- .py::import("rtichoke")
rapi <- .py::import("rapi")
prompt_toolkit <- .py::import("prompt_toolkit")
pygments <- .py::import("pygments")
operator <- .py::import("operator")
sys <- .py::import("sys")
builtins <- .py::import_builtins()

PygmentsLexer <- prompt_toolkit$lexers$PygmentsLexer
Condition <- prompt_toolkit$filters$Condition
KeyBindings <- prompt_toolkit$key_binding$key_bindings$KeyBindings

`|.PyObject` <- function(x, y) .py::py_call(operator$or_, x, y)
`&.PyObject` <- function(x, y) .py::py_call(operator$and_, x, y)

emacs_insert_mode <- prompt_toolkit$filters$emacs_insert_mode
vi_insert_mode <- prompt_toolkit$filters$vi_insert_mode
insert_mode <- vi_insert_mode | emacs_insert_mode
default_focussed <- rtichoke$keybindings$default_focussed
cursor_at_begin <- rtichoke$keybindings$cursor_at_begin
text_is_empty <- rtichoke$keybindings$text_is_empty
main_mode <- Condition(function() {
    app <- prompt_toolkit$application$current$get_app()
    .py::py_copy(app$session$current_mode_name) %in% c("r", "browse")
})

commit_text <- rtichoke$keybindings$commit_text


tidy_code <- function(code) {
    code <- gsub("\r", "", code)[[1]]
    code <- trimws(code, which = "right")
    lines <- unindent(strsplit(code, "\n")[[1]])
    paste(lines, collapse = "\n")
}

leading_spaces <- function(x) regmatches(x, regexpr("^\\s*", x))

unindent <- function(lines) {
    unindented <- character(length(lines))
    for (i in seq_along(lines)) {
        line <- lines[i]
        if (i == 1) {
            indentation <- nchar(leading_spaces(line))
        }
        unindented[i] <- sub(paste0("^\\s{0,", indentation ,"}"), "", line)
    }
    unindented
}

prase_text_complete <- function(code) {
    code <- tidy_code(code)
    if (grepl("\n", code)) {
        return(!is.null(tryCatch(
            builtins$compile(code, "<input>", "exec"),
            error = function(e) NULL
        )))
    } else {
        if (!nzchar(trimws(code))) {
            TRUE
        } else if (xor(substr(code, 1, 1) == "?", substr(code, nchar(code), nchar(code)) == "?")) {
            TRUE
        } else {
            !is.null(tryCatch(
                builtins$compile(code, "<input>", "single"),
                error = function(e) NULL
            ))
        }
    }
}

kb <- KeyBindings()
kb$add("~", filter = insert_mode & default_focussed & cursor_at_begin & text_is_empty & main_mode)(
    function(event) commit_text(event, "reticulate::repl_python(quiet = TRUE)", FALSE)
)

pkb <- rtichoke$keybindings$create_prompt_keybindings(prase_text_complete)

pkb$add("c-d", filter = insert_mode & default_focussed & cursor_at_begin & text_is_empty)(
    function(event) commit_text(event, "exit", FALSE)
)

codeenv <- new.env()

handle_code <- function(code) {
    code <- tidy_code(code)
    if (grepl("\n", code)) {
        # reticulate repl doesn't handle multiline code, we have to execuate it manually
        handle_multiline_code(code)
        codeenv$evaluated <- TRUE
    } else {
        codeenv$evaluated <- FALSE
    }
    code
}

handle_multiline_code <- function(code) {
    # import builtins from reticulate rather than .py because we need globals and locals
    builtins <- reticulate::import_builtins(convert = FALSE)
    locals <- reticulate::py_run_string("locals()")
    globals <- reticulate::py_run_string("globals()")
    lines <- strsplit(code, "\n")[[1]]

    # try spliting the last line
    firstline <- trimws(lines[[1]], which = "right")
    lastline <- lines[[length(lines)]]
    indentation <- leading_spaces(lastline)

    complied <- tryCatch(
        builtins$compile(paste(lines[-length(lines)], collapse = "\n"), "<input>", "exec"),
        error = function(e) e)
    if (indentation == "" && !inherits(complied, "error")) {
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
    key_bindings = kb,
    prompt_key_bindings = pkb
)
