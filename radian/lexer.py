# -*- coding: utf-8 -*-

import re

from pygments.lexer import Lexer, RegexLexer, include, words, do_insertions, bygroups
from pygments.token import Text, Comment, Operator, Keyword, Name, String, \
    Number, Punctuation, Generic


line_re = re.compile('.*?\n')


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

    valid_name = r'(?:`[^`\\]*(?:\\.[^`\\]*)*`)|(?:(?:[a-zA-z]|[_.][^0-9])[\w_.]*)'
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
            (r'<<?-|->>?|-|==|<=|>=|<|>|&&?|!=|\|\|?|\?', Operator),
            (r'\*|\+|\^|/|!|%[^%]*%|=|~|\$|@|:{1,3}', Operator),
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
            (r'\'', String, 'string_squote'),
            (r'(r|R)\'\(', String, 'string_squote_r'),
            (r'(r|R)\'\[', String, 'string_squote_s'),
            (r'(r|R)\'\{', String, 'string_squote_c'),
            (r'(r|R)\'-\(', String, 'string_squote_r1'),
            (r'(r|R)\'-\[', String, 'string_squote_s1'),
            (r'(r|R)\'-\{', String, 'string_squote_c1'),
            (r'(r|R)\'--\(', String, 'string_squote_r2'),
            (r'(r|R)\'--\[', String, 'string_squote_s2'),
            (r'(r|R)\'--\{', String, 'string_squote_c2'),
            (r'(r|R)\'---\(', String, 'string_squote_r3'),
            (r'(r|R)\'---\[', String, 'string_squote_s3'),
            (r'(r|R)\'---\{', String, 'string_squote_c3'),
            (r'(r|R)\'-{4,}\(', String, 'string_squote_r4'),
            (r'(r|R)\'-{4,}\[', String, 'string_squote_s4'),
            (r'(r|R)\'-{4,}\{', String, 'string_squote_c4'),
            (r'\"', String, 'string_dquote'),
            (r'(r|R)\"\(', String, 'string_dquote_r'),
            (r'(r|R)\"\[', String, 'string_dquote_s'),
            (r'(r|R)\"\{', String, 'string_dquote_c'),
            (r'(r|R)\"-\(', String, 'string_dquote_r1'),
            (r'(r|R)\"-\[', String, 'string_dquote_s1'),
            (r'(r|R)\"-\{', String, 'string_dquote_c1'),
            (r'(r|R)\"--\(', String, 'string_dquote_r2'),
            (r'(r|R)\"--\[', String, 'string_dquote_s2'),
            (r'(r|R)\"--\{', String, 'string_dquote_c2'),
            (r'(r|R)\"---\(', String, 'string_dquote_r3'),
            (r'(r|R)\"---\[', String, 'string_dquote_s3'),
            (r'(r|R)\"---\{', String, 'string_dquote_c3'),
            (r'(r|R)\"-{4,}\(', String, 'string_dquote_r4'),
            (r'(r|R)\"-{4,}\[', String, 'string_dquote_s4'),
            (r'(r|R)\"-{4,}\{', String, 'string_dquote_c4'),
            include('builtin_symbols'),
            include('valid_name'),
            include('numbers'),
            include('operators'),
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
        'string_squote': [
            (r'([^\'\\]|\\.)*\'', String, '#pop'),
        ],
        'string_squote_r': [
            (r'(.|\n)*?\)\'', String, '#pop'),
        ],
        'string_squote_s': [
            (r'(.|\n)*?\]\'', String, '#pop'),
        ],
        'string_squote_c': [
            (r'(.|\n)*?\}\'', String, '#pop'),
        ],
        'string_squote_r1': [
            (r'(.|\n)*?\)-\'', String, '#pop'),
        ],
        'string_squote_s1': [
            (r'(.|\n)*?\]-\'', String, '#pop'),
        ],
        'string_squote_c1': [
            (r'(.|\n)*?\}-\'', String, '#pop'),
        ],
        'string_squote_r2': [
            (r'(.|\n)*?\)--\'', String, '#pop'),
        ],
        'string_squote_s2': [
            (r'(.|\n)*?\]--\'', String, '#pop'),
        ],
        'string_squote_c2': [
            (r'(.|\n)*?\}--\'', String, '#pop'),
        ],
        'string_squote_r3': [
            (r'(.|\n)*?\)---\'', String, '#pop'),
        ],
        'string_squote_s3': [
            (r'(.|\n)*?\]---\'', String, '#pop'),
        ],
        'string_squote_c3': [
            (r'(.|\n)*?\}---\'', String, '#pop'),
        ],
        'string_squote_r4': [
            (r'(.|\n)*?\)-{4,}\'', String, '#pop'),
        ],
        'string_squote_s4': [
            (r'(.|\n)*?\]-{4,}\'', String, '#pop'),
        ],
        'string_squote_c4': [
            (r'(.|\n)*?\}-{4,}\'', String, '#pop'),
        ],
        'string_dquote': [
            (r'([^"\\]|\\.)*"', String, '#pop'),
        ],
        'string_dquote_r': [
            (r'(.|\n)*?\)\"', String, '#pop'),
        ],
        'string_dquote_s': [
            (r'(.|\n)*?\]\"', String, '#pop'),
        ],
        'string_dquote_c': [
            (r'(.|\n)*?\}\"', String, '#pop'),
        ],
        'string_dquote_r1': [
            (r'(.|\n)*?\)-\"', String, '#pop'),
        ],
        'string_dquote_s1': [
            (r'(.|\n)*?\]-\"', String, '#pop'),
        ],
        'string_dquote_c1': [
            (r'(.|\n)*?\}-\"', String, '#pop'),
        ],
        'string_dquote_r2': [
            (r'(.|\n)*?\)--\"', String, '#pop'),
        ],
        'string_dquote_s2': [
            (r'(.|\n)*?\]--\"', String, '#pop'),
        ],
        'string_dquote_c2': [
            (r'(.|\n)*?\}--\"', String, '#pop'),
        ],
        'string_dquote_r3': [
            (r'(.|\n)*?\)---\"', String, '#pop'),
        ],
        'string_dquote_s3': [
            (r'(.|\n)*?\]---\"', String, '#pop'),
        ],
        'string_dquote_c3': [
            (r'(.|\n)*?\}---\"', String, '#pop'),
        ],
        'string_dquote_r4': [
            (r'(.|\n)*?\)-{4,}\"', String, '#pop'),
        ],
        'string_dquote_s4': [
            (r'(.|\n)*?\]-{4,}\"', String, '#pop'),
        ],
        'string_dquote_c4': [
            (r'(.|\n)*?\}-{4,}\"', String, '#pop'),
        ],
    }

    def analyse_text(text):
        if re.search(r'[a-z0-9_\])\s]<-(?!-)', text):
            return 0.11
