from pygments.token import Token
from radian.lexer import CustomSLexer

lexer = CustomSLexer()


def cursor_in_string(document):
    tokens = list(lexer.get_tokens(document.text_before_cursor.rstrip()))
    if not tokens:
        return False
    for t, s in reversed(tokens):
        if t is Token.Text and s == "\n":
            continue
        elif t is Token.Error:
            return True
        elif t is Token.Literal.String:
            return True
        else:
            return False
    return False
