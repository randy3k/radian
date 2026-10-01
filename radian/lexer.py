import re

from pygments.lexer import RegexLexer, include
from pygments.token import (
    Comment,
    Error,
    Keyword,
    Name,
    Number,
    Operator,
    Punctuation,
    String,
    Text,
    Token,
)


def _build_raw_string_tokens():
    statements = []
    states = {
        "string_squote": [
            (r"([^\'\\]|\\[\s\S])*\'", String, "#pop"),
            (r"[\s\S]+", Error),
        ],
        "string_dquote": [
            (r'([^"\\]|\\[\s\S])*"', String, "#pop"),
            (r"[\s\S]+", Error),
        ],
    }
    quotes = [("squote", r"\'"), ("dquote", r"\"")]
    dashes = [("", ""), ("1", "-"), ("2", "--"), ("3", "---"), ("4", "-{4,}")]
    brackets = [("r", r"\(", r"\)"), ("s", r"\[", r"\]"), ("c", r"\{", r"\}")]

    for q_name, q_pat in quotes:
        for d_idx, d_pat in dashes:
            for b_key, b_open, b_close in brackets:
                state_name = f"string_{q_name}_{b_key}{d_idx}"
                statements.append((rf"(r|R){q_pat}{d_pat}{b_open}", String, state_name))
                states[state_name] = [
                    (rf"[\s\S]*?{b_close}{d_pat}{q_pat}", String, "#pop"),
                    (r"[\s\S]+", Error),
                ]

    return statements, states


_RAW_STRING_STATEMENTS, _RAW_STRING_STATES = _build_raw_string_tokens()


class CustomSLexer(RegexLexer):
    """
    For S, S-plus, and R source code.

    .. versionadded:: 0.10
    """

    name = 'S'
    aliases = ['splus', 's', 'r']
    filenames = ['*.S', '*.R', '.Rhistory', '.Rprofile', '.Renviron']
    mimetypes = ['text/S-plus', 'text/S', 'text/x-r-source', 'text/x-r',
                 'text/x-R', 'text/x-r-history', 'text/x-r-profile']

    valid_name = r'(?:`[^`\\]*(?:\\.[^`\\]*)*`)|(?![rR][\'"])(?:(?:[a-zA-Z]|[_.][^0-9])[\w_.]*)'
    tokens = {
        'comments': [
            (r'#.*$', Comment.Single),
        ],
        'valid_name': [
            (valid_name, Name),
        ],
        'punctuation': [
            (r'\[{1,2}|\]{1,2}|\(|\)|;|,', Punctuation),
        ],
        'keywords': [
            (r'(if|else|for|while|repeat|in|next|break|return|switch|function)'
             r'(?![\w.])',
             Keyword.Reserved),
            (r'(array|category|character|complex|double|function|integer|list|'
             r'logical|matrix|numeric|vector|data.frame|c)'
             r'(?![\w.])',
             Keyword.Type),
            (r'(library|require|attach|detach|source)'
             r'(?![\w.])',
             Keyword.Namespace)
        ],
        'operators': [
            (r'<<?-|->>?|-|==|<=|>=|<|>|&&?|!=|\|>|\|\|?|\?', Operator),
            (r'\*|\+|\^|/|!|%[^%]*%|=|~|\$|@|:{1,3}|\\', Operator),
        ],
        'builtin_symbols': [
            (r'(NULL|NA(_(integer|real|complex|character)_)?|'
             r'letters|LETTERS|Inf|TRUE|FALSE|NaN|pi|\.\.(\.|[0-9]+))'
             r'(?![\w.])',
             Keyword.Constant),
            (r'(T|F)\b', Name.Builtin.Pseudo),
        ],
        'numbers': [
            # hex number
            (r'0[xX][a-fA-F0-9]+([pP][0-9]+)?[Li]?', Number.Hex),
            # decimal number
            (r'[+-]?([0-9]+(\.[0-9]+)?|\.[0-9]+|\.)([eE][+-]?[0-9]+)?[Li]?',
             Number),
        ],
        'statements': [
            include('comments'),
            # whitespaces
            (r'\s+', Text),
            (r"\'", String, "string_squote"),
            (r'\"', String, "string_dquote"),
            include('builtin_symbols'),
            include('valid_name'),
            include('numbers'),
            include('operators'),
            *_RAW_STRING_STATEMENTS,
        ],
        'root': [
            # calls:
            include('keywords'),
            include('punctuation'),
            (r'r%s\s*(?=\()' % valid_name, Keyword.Pseudo),
            include('statements'),

            # blocks:
            (r'\{|\}', Punctuation),
            # (r'\{', Punctuation, 'block'),
            (r'.', Text),
        ],
        **_RAW_STRING_STATES,
    }

    def analyse_text(text):
        if re.search(r'[a-z0-9_\])\s]<-(?!-)', text):
            return 0.11


_lexer = CustomSLexer()
_cursor_in_string_cache = (None, False)


def cursor_in_string(document):
    global _cursor_in_string_cache
    text = document.text_before_cursor
    if "'" not in text and '"' not in text:
        return False
    if _cursor_in_string_cache[0] == text:
        return _cursor_in_string_cache[1]
    tokens = list(_lexer.get_tokens_unprocessed(text))
    if not tokens:
        res = False
    else:
        _, last_token, _ = tokens[-1]
        if last_token is Token.Error:
            res = True
        elif last_token is Token.Literal.String:
            res = sum(1 for _, t, _ in tokens if t is Token.Literal.String) % 2 == 1
        else:
            res = False
    _cursor_in_string_cache = (text, res)
    return res


