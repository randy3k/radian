# register a custom prompt which evaluates R expressions in an sandbox environment

rchitect <- getOption("rchitect_environment")
import <- rchitect$import
py_call <- rchitect$py_call
py_copy <- rchitect$py_copy

radian <- import("radian")
prompt_toolkit <- import("prompt_toolkit")
pygments <- import("pygments")
operator <- import("operator")

PygmentsLexer <- prompt_toolkit$lexers$PygmentsLexer
KeyBindings <- prompt_toolkit$key_binding$key_bindings$KeyBindings

`|.PyObject` <- function(x, y) py_call(operator$or_, x, y)
`&.PyObject` <- function(x, y) py_call(operator$and_, x, y)

emacs_insert_mode <- prompt_toolkit$filters$emacs_insert_mode
vi_insert_mode <- prompt_toolkit$filters$vi_insert_mode
insert_mode <- vi_insert_mode | emacs_insert_mode
cursor_at_begin <- radian$keybindings$cursor_at_begin
default_focussed <- radian$keybindings$default_focussed

kb <- KeyBindings()
kb$add("#", filter = insert_mode & default_focussed & cursor_at_begin)(
    function(event) event$app$session$change_mode("env")
)

pkb <- KeyBindings()
pkb$add("backspace", filter = insert_mode & default_focussed & cursor_at_begin)(
    function(event) event$app$session$change_mode("r")
)

app <- radian$get_app()
env <- new.env(parent = emptyenv())
app$session$register_mode(
    "env",
    native = FALSE,
    message = "env> ",
    insert_new_line = TRUE,
    lexer = PygmentsLexer(pygments$lexers$r$SLexer),
    on_done = function(session) {
        text <- py_copy(session$default_buffer$text)
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
