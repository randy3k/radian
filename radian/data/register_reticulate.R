# register reticulate prompt

rchitect <- getOption("rchitect_environment")
import <- rchitect$import
import_builtins <- rchitect$import_builtins
py_call <- rchitect$py_call
py_eval <- rchitect$py_eval
py_copy <- rchitect$py_copy
tuple <- rchitect$tuple
dict <- rchitect$dict
`$.PyObject` <- rchitect$`$.PyObject`
`[.PyObject` <- rchitect$`[.PyObject`


radian <- import("radian")
prompt_toolkit <- import("prompt_toolkit")
pygments <- import("pygments")
operator <- import("operator")
code <- import("code")
jedi <- tryCatch(import("jedi"), error = function(e) NULL)
builtins <- import_builtins()
len <- py_copy("function", builtins$len)
locals <- reticulate::py_run_string("locals()")
globals <- reticulate::py_run_string("globals()")
compile_command <- code$compile_command

PygmentsLexer <- prompt_toolkit$lexers$PygmentsLexer
Condition <- prompt_toolkit$filters$Condition
Completion <- prompt_toolkit$completion$Completion
Completer <- prompt_toolkit$completion$Completer
KeyBindings <- prompt_toolkit$key_binding$key_bindings$KeyBindings

PythonCompleter <- builtins$type(
    builtins$str("PythonCompleter"),
    tuple(Completer),
    dict(
        get_completions = function(self, document, complete_event) {
            script <- NULL
            word <- document$get_word_before_cursor()
            if (complete_event$completion_requested || len(word) >= 3) {
                script <- tryCatch({
                    jedi$Interpreter(
                        document$text,
                        column = document$cursor_position_col,
                        line = document$cursor_position_row + 1L,
                        path = "input-text",
                        namespaces = list(locals, globals)
                    )
                }, error = function(e) NULL)
            }

            if (is.null(script)) {
                list()
            } else {
                completions <- script$completions()
                ret <- list()
                for (i in seq_len(len(completions))) {
                    c <- completions[i - 1L]
                    ret[[i]] <- Completion(
                        c$name_with_symbols, nchar(c$complete) - nchar(c$name_with_symbols))
                }
                ret
            }
        }
    )
)

`|.PyObject` <- function(x, y) py_call(operator$or_, x, y)
`&.PyObject` <- function(x, y) py_call(operator$and_, x, y)

emacs_insert_mode <- prompt_toolkit$filters$emacs_insert_mode
vi_insert_mode <- prompt_toolkit$filters$vi_insert_mode
insert_mode <- vi_insert_mode | emacs_insert_mode
default_focussed <- radian$keybindings$default_focussed
cursor_at_begin <- radian$keybindings$cursor_at_begin
text_is_empty <- radian$keybindings$text_is_empty
main_mode <- Condition(function() {
    app <- prompt_toolkit$application$current$get_app()
    app$session$current_mode_name %in% c("r", "browse")
})

commit_text <- radian$keybindings$commit_text

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

py_is_null <- function(x) {
    py_copy(operator$is_(x, py_eval("None")))
}

prase_text_complete <- function(code) {
    code <- tidy_code(code)
    if (grepl("\n", code)) {
        return(tryCatch(
            !py_is_null(compile_command(code, "<input>", "exec")),
            error = function(e) TRUE
        ))
    } else {
        if (!nzchar(trimws(code))) {
            TRUE
        } else if (xor(substr(code, 1, 1) == "?", substr(code, nchar(code), nchar(code)) == "?")) {
            TRUE
        } else {
            tryCatch(
                !py_is_null(compile_command(code, "<input>", "single")),
                error = function(e) TRUE
            )
        }
    }
}

kb <- KeyBindings()
kb$add("~", filter = insert_mode & default_focussed & cursor_at_begin & text_is_empty & main_mode)(
    function(event) {
        commit_text(event, "reticulate::repl_python(quiet = TRUE)", FALSE)
    }
)

pkb <- radian$keybindings$create_prompt_keybindings(prase_text_complete)

pkb$add("c-d", filter = insert_mode & default_focussed & cursor_at_begin & text_is_empty)(
    function(event) commit_text(event, "exit", FALSE)
)

pkb$add("backspace", filter = insert_mode & default_focussed & cursor_at_begin & text_is_empty)(
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
    # we need reticulate::py_last_error, so we have to use builtins from reticulate
    builtins <- reticulate::import_builtins()

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

app <- radian$get_app()
app$session$register_mode(
    "reticulate",
    native = FALSE,
    on_done = function(session) handle_code(session$default_buffer$text),
    return_result = function(result) !codeenv$evaluated,
    activator = function(session) reticulate:::py_repl_active(),
    message = function() app$session$prompt_text,
    multiline = TRUE,
    insert_new_line = TRUE,
    lexer = PygmentsLexer(pygments$lexers$python$PythonLexer),
    key_bindings = kb,
    prompt_key_bindings = pkb,
    completer = if (is.null(jedi)) NULL else PythonCompleter()
)
