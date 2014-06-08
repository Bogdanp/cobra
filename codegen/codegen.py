"""
TODO: Make assignment an expression.
"""

import ast

from lexer import *
from parser import *


class Codegen(object):
    def __init__(self, parser):
        self.parser = parser

    """
    NFUNDECL
    NFWDDECL
    """
    def transform_function_declaration(self, children):
        (_, name, params), body = children[:3], children[3]

        params = self.transform(params)
        body = self.transform(body)

        return ast.FunctionDef(
            name, params, body, []
        )

    """
    NPLIST
    """
    def transform_parameter_list(self, children):
        return ast.arguments(
            map(lambda name: self.transform_identifier([name], param=True), children),
            None, None, [],
        )

    """
    NBLOCK
    """
    def transform_statement(self, children):
        if isinstance(children[0], tuple):
            return self.transform(children[1])
        node = self.transform(children)

        if isinstance(node, ast.Assign) or \
           isinstance(node, ast.If) or \
           isinstance(node, ast.While) or \
           isinstance(node, ast.Return):
            return node
        else:
            return ast.Expr(node)

    def transform_block(self, children):
        return map(self.transform_statement, children)

    """
    NDECL
    """
    def transform_variable_declaration(self, children):
        name = self.transform_identifier(children, store=True)
        return ast.Assign([name], self.transform_identifier(["None"], load=True))

    """
    NIF
    NELIF
    """
    def transform_if(self, children):
        (cond, body), orelse = children[:2], children[2:]

        cond = self.transform(cond)
        body = self.transform(body)

        if orelse:
            orelse = self.transform(orelse[0])

            if isinstance(orelse, ast.If):
                orelse = [orelse]

            return ast.If(cond, body, orelse)
        return ast.If(cond, body, [])

    """
    NELSE
    """
    def transform_else(self, children):
        return self.transform(children[0])

    """
    NFOR
    """
    def transform_for(self, children):
        init, cond, term, body = children

        init = self.transform(init)
        cond = self.transform(cond)
        term = self.transform(term)
        body = self.transform(body)

        print init
        print cond
        print term
        print body

    """
    NWHILE
    """
    def transform_while(self, children):
        cond, body = children
        cond = self.transform(cond)
        body = self.transform(body)
        return ast.While(cond, body, [])

    """
    NRETURN
    """
    def transform_return(self, children):
        if children:
            return ast.Return(self.transform(children[0]))
        return ast.Return()

    """
    NCALL
    """
    def transform_function_call(self, children):
        name, arguments = children[0], children[1:]
        name = self.transform_identifier([name], load=True)
        arguments = map(self.transform, arguments)

        return ast.Call(
            name, arguments,
            [], None, None
        )

    """
    NLUNARY
    """
    def transform_lunary(self, children):
        op, e = children
        bop = {
            "++": ast.Add,
            "--": ast.Sub,
        }
        uop = {
            "+": ast.UAdd,
            "-": ast.USub,
            "!": ast.Not,
            "~": ast.Invert,
        }

        if op in bop:
            name = self.transform(e)
            namer = self.transform(e)
            name.ctx = ast.Store()
            namer.ctx = ast.Load()

            return ast.BinOp(namer, bop[op](), ast.Num(1))

        return ast.UnaryOp(uop[op](), self.transform(e))

    """
    NRUNARY
    """
    def transform_runary(self, children):
        op, e = children
        name = self.transform(e)
        name.ctx = ast.Load()

        return name

    """
    NBINARY
    """
    def transform_assign(self, op, e1, e2):
        op = {
            "=":  None,
            "+=": ast.Add,
            "-=": ast.Sub,
            "*=": ast.Mult,
            "/=": ast.Div,
        }[op]

        name = self.transform(e1)
        name.ctx = ast.Store()
        expression = self.transform(e2)

        if op is None:
            return ast.Assign([name], expression)

        namer = self.transform(e1)
        namer.cts = ast.Load()

        return ast.Assign([name], ast.BinOp(namer, op(), expression))

    def transform_op(self, op, e1, e2):
        binop = {
            "+": ast.Add,
            "-": ast.Sub,
            "*": ast.Mult,
            "/": ast.Div,
            "%": ast.Mod,
            "&": ast.BitAnd,
            "|": ast.BitOr,
            "^": ast.BitXor,

            "<<": ast.LShift,
            ">>": ast.RShift,
        }
        cmpop = {
            "==": ast.Eq,
            "!=": ast.NotEq,
            ">=": ast.GtE,
            "<=": ast.LtE,

            "<": ast.Lt,
            ">": ast.Gt,
        }
        boolop = {
            "&&": ast.And,
            "||": ast.Or,
        }

        if op in binop:
            return ast.BinOp(
                self.transform(e1), binop[op](), self.transform(e2))

        if op in cmpop:
            return ast.Compare(
                self.transform(e1), [cmpop[op]()], [self.transform(e2)])

        if op in boolop:
            return ast.BoolOp(
                self.transform(e1), boolop[op](), self.transform(e2))

    def transform_binary(self, children):
        op, e1, e2 = children

        try:
            return self.transform_assign(op, e1, e2)
        except KeyError:
            return self.transform_op(op, e1, e2)

    """
    TIDENTIFIER
    """
    def transform_identifier(self, children, param=False, load=False, store=False):
        name = children[0]

        if param:
            return ast.Name(name, ast.Param())

        if store:
            return ast.Name(name, ast.Store())

        return ast.Name(name, ast.Load())

    """
    TNUMBER
    """
    def transform_number(self, children):
        return ast.Num(children[0])

    """
    TCHARACTER
    TSTRING
    """
    def transform_string(self, children):
        return ast.Str(children[0])

    def transform(self, node):
        kind, children = node[0], node[1:]

        return {
            NFUNDECL:    self.transform_function_declaration,
            NFWDDECL:    self.transform_function_declaration,
            NPLIST:      self.transform_parameter_list,
            NBLOCK:      self.transform_block,
            NDECL:       self.transform_variable_declaration,
            NIF:         self.transform_if,
            NELIF:       self.transform_if,
            NELSE:       self.transform_else,
            NFOR:        self.transform_for,
            NWHILE:      self.transform_while,
            NRETURN:     self.transform_return,
            NCALL:       self.transform_function_call,
            NLUNARY:     self.transform_lunary,
            NRUNARY:     self.transform_runary,
            NBINARY:     self.transform_binary,

            TIDENTIFIER: self.transform_identifier,
            TNUMBER:     self.transform_number,
            TCHARACTER:  self.transform_string,
            TSTRING:     self.transform_string,
        }[kind](children)

    def gen_module(self, main=False):
        nodes = self.parser.parse()
        module = []

        for node in nodes:
            module.append(self.transform(node))

        if main:
            module.append(ast.Expr(ast.Call(
                self.transform_identifier(["main"], load=True),
                [], [], None, None,
            )))

        module = ast.Module(module)
        module.lineno = 1
        module.col_offset = 0

        return ast.fix_missing_locations(module)
