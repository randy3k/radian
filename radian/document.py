from pygments.token import Token
from radian.lexer import CustomSLexer

lexer = CustomSLexer()


def cursor_in_string(document):
    tokens = list(lexer.get_tokens_unprocessed(document.text_before_cursor))
    if not tokens:
        return False
    _, last_token, _ = tokens[-1]
    if last_token is Token.Error:
        return True
    elif last_token is Token.Literal.String:
        return sum(1 for _, t, _ in tokens if t is Token.Literal.String) % 2 == 1
    return False
