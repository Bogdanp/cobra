from .core import *


class Parser(StandardParser):
    def parse_paren_expression(self):
        self.consume(TOPERATOR, "(")
        e = self.parse_expression()
        self.consume(TOPERATOR, ")")
        return e

    def parse_expression(self):
        def require(type_, value=None, move=0):
            self.move(move)

            if not self.isa(type_, value):
                self.move(-move)
                raise Continue()

        def term(type_):
            def parser():
                require(type_)
                return (type_, self.consume(type_))
            return parser

        def lunary(value):
            def parser():
                require(TOPERATOR, value)
                self.consume(TOPERATOR)
                return (NLUNARY, value, primary())
            return parser

        def runary(value):
            def parser():
                require(TOPERATOR, value, 1)

                self.drop(0, 1)
                self.move(-1)

                return (NRUNARY, value, primary())
            return parser

        def paren():
            require(TOPERATOR, "(")
            return self.parse_paren_expression()

        def funcall():
            require(TIDENTIFIER)
            require(TOPERATOR, "(", 1)
            self.move(-1)
            fun = self.consume(TIDENTIFIER)
            self.consume(TOPERATOR, "(")

            parameters = []

            while not self.isa(TOPERATOR, ")"):
                parameters.append(self.parse_expression())
                self.ignore(TOPERATOR, ",")

            self.consume(TOPERATOR, ")")

            return tuple([NCALL, fun] + parameters)

        def primary():
            # Highest precedence at the top.
            return self.alternative((
                paren,
                funcall,
                runary("--"),
                runary("++"),
                lunary("!"),
                lunary("~"),
                lunary("&"),
                lunary("+"),
                lunary("-"),
                lunary("--"),
                lunary("++"),
                term(TIDENTIFIER),
                term(TNUMBER),
                term(TCHARACTER),
                term(TSTRING),
            ))

        def binary(e1, mp):
            "Simple precedence climbing."

            while self.isin(TOPERATOR, BINARY_OPERATORS) and precedence(self.value) >= mp:
                op, e2 = self.consume(TOPERATOR), primary()

                # All binary operators are assumed to be left-associative.
                while self.isa(TOPERATOR) and precedence(self.value) >= precedence(op):
                    e2 = binary(e2, precedence(self.value))

                e1 = (NBINARY, op, e1, e2)

            return e1

        return binary(primary(), 0)

    def parse_if(self):
        kind = globals()["N" + self.consume(TKEYWORD).upper()]
        cond = self.parse_paren_expression()

        if self.isa(TOPERATOR, ";"):
            return (NIF, cond)

        block = self.parse_block()

        if self.isa(TKEYWORD, "else if"):
            return (kind, cond, block, self.parse_if())

        if self.ignore(TKEYWORD, "else"):
            return (kind, cond, block, (NELSE, self.parse_block()))

        return (kind, cond, block)

    def parse_for(self):
        self.consume(TKEYWORD, "for")
        self.consume(TOPERATOR, "(")

        e1, e2, e3 = None, None, None

        if not self.isa(TOPERATOR, ";"):
            e1 = self.parse_expression()

        self.consume(TOPERATOR, ";")

        if not self.isa(TOPERATOR, ";"):
            e2 = self.parse_expression()

        self.consume(TOPERATOR, ";")

        if not self.isa(TOPERATOR, ")"):
            e3 = self.parse_expression()

        self.consume(TOPERATOR, ")")

        if self.isa(TOPERATOR, ";"):
            return (NFOR, e1, e2, e3)

        return (NFOR, e1, e2, e3, self.parse_block())

    def parse_while(self):
        self.consume(TKEYWORD, "while")
        self.consume(TOPERATOR, "(")
        condition = self.parse_expression()
        self.consume(TOPERATOR, ")")

        if self.ignore(TOPERATOR, ";"):
            return (NWHILE, condition)
        return (NWHILE, condition, self.parse_block())

    def parse_return(self):
        self.consume(TKEYWORD, "return")
        done = self.ignore(TOPERATOR, ";")

        if done:
            return (NRETURN,)

        return (NRETURN, self.parse_expression())

    def parse_variable(self):
        self.ignore(TKEYWORD, "const")
        self.consume(TTYPE)

        while self.isa(TOPERATOR, "*"):
            self.consume(TOPERATOR, "*")

        variable = self.consume(TIDENTIFIER)

        if self.isa(TOPERATOR, "["):
            self.consume(TOPERATOR, "[")
            self.consume(TNUMBER)
            self.consume(TOPERATOR, "]")

        return variable

    def parse_declaration(self):
        variable = self.parse_variable()

        if self.isa(TOPERATOR, "="):
            self.move(-1)

            if self.isa(TOPERATOR, "]"):
                self.drop(2, 1)
                self.move(-3)

            return (NDECL, variable), self.parse_expression()

        return (NDECL, variable)

    def parse_statement(self):
        def declaration():
            if not self.isa(TTYPE):
                raise Continue()
            return self.parse_declaration()

        def keyword():
            if not self.isa(TKEYWORD):
                raise Continue()

            try:
                return {
                    "if": self.parse_if,
                    "for": self.parse_for,
                    "while": self.parse_while,
                    "return": self.parse_return,
                }[self.value]()
            except KeyError:
                raise UnexpectedToken("unexpected KEYWORD " + self.value)

        result = self.alternative((
            declaration,
            keyword,
            self.parse_expression,
        ))

        if result[0] not in (NIF, NELIF, NELSE, NFOR, NWHILE):
            self.consume(TOPERATOR, ";")

        return result

    def parse_block(self):
        statements = []

        if not self.isa(TOPERATOR, "{"):
            return (NBLOCK, self.parse_statement())

        self.consume(TOPERATOR, "{")

        while not self.isa(TOPERATOR, "}"):
            statements.append(self.parse_statement())

        self.consume(TOPERATOR, "}")

        return tuple([NBLOCK] + statements)

    def parse_parameter_list(self):
        parameters = []

        self.consume(TOPERATOR, "(")

        while not self.isa(TOPERATOR, ")"):
            parameters.append(self.parse_variable())
            self.ignore(TOPERATOR, ",")

        self.consume(TOPERATOR, ")")

        return tuple([NPLIST] + parameters)

    def parse_toplevel(self):
        type_ = self.consume(TTYPE)
        identifier = self.consume(TIDENTIFIER)
        parameters = self.parse_parameter_list()

        if self.ignore(TOPERATOR, ";"):
            return (NFWDDECL, type_, identifier, parameters)
        return (NFUNDECL, type_, identifier, parameters, self.parse_block())
