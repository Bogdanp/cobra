from lexer import *


# Possible node types.
for N in ("FUNDECL", "FWDDECL", "PLIST", "BLOCK", "DECL",
          "IF", "ELIF", "ELSE", "FOR", "WHILE", "RETURN",
          "CALL", "LUNARY", "RUNARY", "BINARY"):
    locals()["N" + N] = N


def print_tree(node, indentation=0):
    "Pretty-prints a given AST."

    if isinstance(node, tuple):
        type_, children = node[0], list(node[1:])
    else:
        type_, children = str(node), []

    if isinstance(type_, tuple):
        map(lambda n: print_tree(n, indentation), node)
    else:
        print " " * indentation + type_

        for child in children:
            print_tree(child, indentation + 1)


class Continue(Exception):
    "Raised when an alternative parser should be skipped."


class ParserError(Exception):
    pass


class UnexpectedToken(ParserError):
    "Raised when an unexpected token was encountered."


class StandardParser(object):
    """A grouping of methods that aids with parsing Token lists."""

    def __init__(self, tokens):
        self.cursor = 0
        self.tokens = tokens

    @property
    def rest(self):
        "The rest of the tokens."
        return self.tokens[self.cursor:]

    @property
    def token(self):
        "The current token."
        return self.tokens[self.cursor]

    @property
    def type_(self):
        "The type of the current token."
        return self.token.type_

    @property
    def value(self):
        "The value of the current token."
        return self.token.value

    def move(self, by):
        "Moves the cursor by the given amount."
        self.cursor += by

    def drop(self, l, r):
        "Drops tokens from the list."
        del self.tokens[self.cursor - l:self.cursor + r]

    def isa(self, type_, value=None):
        "Checks if the current token has the given type and value."
        if value is not None:
            return (self.type_ == type_ and
                    self.value == value)

        return self.type_ == type_

    def isin(self, type_, values):
        """Checks if the current token has the given type and if its
        value is in the given list."""
        return any(map(lambda value: self.isa(type_, value), values))

    def consume(self, type_, value=None):
        """Consumes the current token, raising an UnexpectedToken
        exception if the token does not match the given type and
        value."""
        if not self.isa(type_, value):
            raise UnexpectedToken("got {0}{2}, expected {1}{3}".format(
                self.type_, type_,
                "" if self.value is None else " {}".format(self.value),
                "" if      value is None else " {}".format(value),
            ))

        value = self.value

        self.move(1)

        return value

    def ignore(self, type_, value=None):
        """Consumes the current token iff it matches the given type and
        value. Silently ignores it otherwise.
        """
        if self.isa(type_, value):
            return self.consume(type_, value)

        return None

    def alternative(self, alternatives):
        """Given a list functions, it calls each function in sequence
        until one of them succeeds."""
        for parser in alternatives:
            try:
                return parser()
            except Continue:
                pass

        raise UnexpectedToken("unexpected {} {}".format(
            self.type_, self.value
        ))

    def parse_toplevel(self):
        """This is the parser's entry point. All subclasses must
        override this."""
        raise NotImplementedError()

    def parse(self):
        "Parses every top-level statement it finds."
        try:
            while True:
                yield self.parse_toplevel()
        except IndexError:
            pass
