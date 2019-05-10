# register reticulate prompt

getOption("rchitect.py_tools")$attach()

radian <- import("radian")
prompt_toolkit <- import("prompt_toolkit")
pygments <- import("pygments")
operator <- import("operator")
code <- import("code")
builtins <- import_builtins()
len <- builtins$len

KeyBindings <- prompt_toolkit$key_binding$key_bindings$KeyBindings

insert_mode <- radian$key_bindings$insert_mode
default_focussed <- radian$key_bindings$default_focussed
cursor_at_begin <- radian$key_bindings$cursor_at_begin
text_is_empty <- radian$key_bindings$text_is_empty
preceding_text <- radian$key_bindings$preceding_text
prompt_mode <- radian$key_bindings$prompt_mode
main_mode <- prompt_mode("r") | prompt_mode("browse")

commit_text <- radian$key_bindings$commit_text
newline <- radian$key_bindings$newline

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
        unindented[i] <- sub(paste0("^\\s{0,", indentation, "}"), "", line)
    }
    unindented
}


kb <- KeyBindings()
kb$add("~", filter = insert_mode & default_focussed & cursor_at_begin & text_is_empty & main_mode)(
    function(event) {
        commit_text(event, "reticulate::repl_python(quiet = TRUE)", FALSE)
    })


prase_text_complete <- radian$reticulate$prase_text_complete
pkb <- radian$key_bindings$create_prompt_key_bindings(prase_text_complete)

pkb$add("c-d", filter = insert_mode & default_focussed & cursor_at_begin & text_is_empty)(
    function(event) commit_text(event, "exit", FALSE)
)

pkb$add("backspace", filter = insert_mode & default_focussed & cursor_at_begin & text_is_empty)(
    function(event) commit_text(event, "exit", FALSE)
)

pkb$add("enter", filter = insert_mode & default_focussed & preceding_text(".*:"))(
    function(event) {
        newline(event, chars = list(":"))
    }
)

handle_code <- function(code) {
    code <- tidy_code(code)
    if (grepl("\n", code)) {
        # reticulate repl doesn't handle multiline code, we have to execuate it manually
        handle_multiline_code(code)
        return(NULL)
    }
    return(code)
}

handle_multiline_code <- function(code) {
    # we need reticulate::py_last_error, so we have to use builtins from reticulate
    builtins <- reticulate::import_builtins()
    lines <- strsplit(code, "\n")[[1]]

    # try spliting the last line
    firstline <- trimws(lines[[1]], which = "right")
    lastline <- lines[[length(lines)]]
    indentation <- leading_spaces(lastline)

    locals <- reticulate::py_run_string("locals()")
    globals <- reticulate::py_run_string("globals()")

    complied <- tryCatch(
        builtins$compile(paste(lines[-length(lines)], collapse = "\n"), "<input>", "exec"),
        error = function(e) e
    )
    if (indentation == "" && !inherits(complied, "error")) {
        output <- tryCatch({
            builtins$eval(complied, locals, globals)
            builtins$eval(builtins$compile(lastline, "<input>", "single"), locals, globals)
        },
        error = function(e) e
        )
    } else {
        output <- tryCatch(
            builtins$eval(builtins$compile(code, "<input>", "exec"), locals, globals),
            error = function(e) e
        )
    }
    if (inherits(output, "error")) {
        error <- reticulate::py_last_error()
        message(paste(error$type, error$value, sep = ": "))
    }
}


if (is.null(tryCatch(import("jedi"), error = function(e) NULL))) {
    python_completer <- NULL
} else {
    Completer <- prompt_toolkit$completion$Completer
    Completion <- prompt_toolkit$completion$Completion
    get_reticulate_completions <- radian$reticulate$get_reticulate_completions
    PythonCompleter <- builtins$type(
        py_call(builtins$str, "PythonCompleter"),
        tuple(Completer),
        dict(
            get_completions = function(self, document, complete_event) {
                completions <- get_reticulate_completions(document, complete_event)
                lapply(completions, function(c) {
                    Completion(c$name_with_symbols, nchar(c$complete) - nchar(c$name_with_symbols))
                })
            }
        )
    )
    python_completer <- PythonCompleter()
}


app <- radian$get_app()
app$session$register_mode(
    "reticulate",
    native = FALSE,
    on_done = function(session) handle_code(session$default_buffer$text),
    activator = function(session) reticulate:::py_repl_active(),
    message = function() app$session$prompt_text,
    multiline = TRUE,
    insert_new_line = TRUE,
    lexer = prompt_toolkit$lexers$PygmentsLexer(pygments$lexers$python$PythonLexer),
    key_bindings = kb,
    prompt_key_bindings = pkb,
    completer = python_completer
)
