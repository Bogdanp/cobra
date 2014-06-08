import re

from collections import namedtuple


Token = namedtuple("Token", ["type_", "value"])

# Possible token types.
for T in ("NUMBER", "CHARACTER", "STRING",
          "TYPE", "KEYWORD", "OPERATOR",
          "IDENTIFIER"):
    locals()["T" + T] = T

# [(operator, precedence)]
_BINARY_OPERATORS = (
    ("*",  12),
    ("/",  12),
    ("%",  12),
    ("+",  11),
    ("-",  11),
    ("<<", 10),
    (">>", 10),
    ("==",  8),
    ("!=",  8),
    (">=",  8),
    ("<=",  8),
    (">",   8),
    ("<",   8),
    ("&",   7),
    ("^",   6),
    ("|",   5),
    ("&&",  4),
    ("||",  3),
    ("=",   1),
    ("-=",  1),
    ("+=",  1),
    ("*=",  1),
    ("/=",  1),
)
BINARY_OPERATORS = map(lambda (x, _): x, _BINARY_OPERATORS)


def precedence(op):
    """Returns the precendence of the given operator. Returns None when
    the operator couldn't be found."""
    for operator, precedence in _BINARY_OPERATORS:
        if operator.replace("\\", "") == op:
            return precedence

    return None


def lex(code):
    """Given an arbitrary piece of code, this returns a tuple containing
    a boolean value representing whether or not lexical analysis succeeded and
    a list of Tokens."""

    types = ("char", "int", "float", "void",)
    keywords = ("if", "else if", "else", "for", "while", "return", "const",)
    operators = ("==", "!=", ">=", "<=", "<<", ">>", "\-=", "\+=", "\*=", "/=",
                 "\&\&", "\|\|", "\+\+", "\-\-", ">", "<", "&", "\^", "\|",
                 "\+", "-", "\*", "/", "%", "!", "~", "=", ";", ",", "\[",
                 "\(", "\{", "\]", "\)", "}",)

    tokens, remainder = re.Scanner([
        # Comments
        (r"/\*.*?\*/",              None),
        (r"//.*$",                  None),

        # Numbers
        (r"([1-9]\d*|0)?\.\d+",     lambda _, token: Token(TNUMBER, float(token))),
        (r"([1-9]\d*)",             lambda _, token: Token(TNUMBER, int(token))),
        (r"0x[0-F]+",               lambda _, token: Token(TNUMBER, int(token, base=16))),
        (r"0",                      lambda _, token: Token(TNUMBER, int(token))),

        # Characters and strings
        (r"'(\'|[^'])'",            lambda _, token: Token(TCHARACTER, token[1:-1])),
        (r'"(\"|[^"])*?"',          lambda _, token: Token(TSTRING, token[1:-1])),

        # Types
        (r"|".join(types),          lambda _, token: Token(TTYPE, token)),

        # Keywords
        (r"|".join(keywords),       lambda _, token: Token(TKEYWORD, token)),

        # Operators
        (r"|".join(operators),      lambda _, token: Token(TOPERATOR, token)),

        # Identifiers
        (r"[a-zA-Z_][0-9a-zA-Z_]*", lambda _, token: Token(TIDENTIFIER, token)),

        # Whitespace
        (r"[\r\t\n ]*",             None),
    ], re.DOTALL | re.MULTILINE).scan(code)

    if remainder:
        return False, "failed to lex: " + remainder

    return True, tokens
