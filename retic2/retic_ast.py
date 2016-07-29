import ast
from . import typing
from .typing import retic_prefix


retic_prefix('typing')

typing.nominal()


class Type: pass

class Dyn(Type): 
    def to_ast(self, lineno:int, col_offset:int)->ast.expr:
        return ast.Name(id='object', ctx=ast.Load(), lineno=lineno, col_offset=col_offset)
    def __str__(self)->str:
        return 'any'

@typing.fields({'type': str})
class Primitive(Type): 
    def to_ast(self, lineno:int, col_offset:int)->ast.expr:
        return ast.Name(id=self.type, ctx=ast.Load(), lineno=lineno, col_offset=col_offset)
    def __str__(self)->str:
        return self.type

class Int(Primitive):
    def __init__(self):
        self.type = 'int'

class Bool(Primitive):
    def __init__(self):
        self.type = 'bool'

class Str(Primitive):
    def __init__(self):
        self.type = 'str'

class Void(Primitive):
    def __init__(self):
        self.type = 'None'


@typing.constructor_fields
class Function(Type):
    def __init__(self, froms:'ArgTypes', to:Type):
        self.froms = froms
        self.to = to

    def to_ast(self, lineno:int, col_offset:int)->ast.expr:
        return ast.Name(id='callable', ctx=ast.Load(), lineno=lineno, col_offset=col_offset)

    def __str__(self)->str:
        return 'Function[{},{}]'.format(self.froms, self.to)

@typing.constructor_fields
class List(Type):
    def __init__(self, elts: Type):
        self.elts = elts

    def to_ast(self, lineno:int, col_offset:int)->ast.expr:
        return ast.Name(id='list', ctx=ast.Load(), lineno=lineno, col_offset=col_offset)

    def __str__(self)->str:
        return 'List[{}]'.format(self.elts)





# ArgTypes is the LHS of the function type arrow. We should _not_ use
# this on the inside of functions to determine what the type env or
# required transient checks are.
class ArgTypes: 
    def match(self, nargs: int)->typing.List[Type]:
        raise Exception('abstract')

    def can_match(self, nargs: int)->bool:
        raise Exception('abstract')

class ArbAT(ArgTypes):
    def match(self, nargs: int)->typing.List[Type]:
        return [Dyn()] * nargs

    def can_match(self, nargs: int)->bool:
        return True
    def __str__(self)->str:
        return '...'

@typing.constructor_fields
class PosAT(ArgTypes):
    def __init__(self, types: typing.List[Type]):
        self.types = types

    def match(self, nargs: int)->typing.List[Type]:
        return self.types[:nargs]

    def can_match(self, nargs: int)->bool:
        return len(self.types) == nargs
    def __str__(self)->str:
        return str(self.types)

class ContextTag: pass

@typing.constructor_fields
class Check(ast.expr):
    def __init__(self, value: ast.expr, type: Type, lineno:int, col_offset:int):
        self.value = value
        self.type = type
        self.lineno = lineno
        self.col_offset = col_offset

    def to_ast(self)->ast.expr:
        return ast.Call(func=ast.Name(id='_retic_check', ctx=ast.Load()), args=[self.value, self.type.to_ast()], 
                        keywords=[], starargs=None, kwargs=None)
        
@typing.constructor_fields
class BlameCheck(ast.expr):
    def __init__(self, value: ast.expr, type: Type, owner: ast.expr, cxt_tag: ContextTag):
        self.value = value
        self.type = type
        self.owner = owner
        self.cxt_tag = tag

@typing.constructor_fields
class BlameCast(ast.expr):
    def __init__(self, value: ast.expr, src: Type, trg: Type, lineno: int):
        self.value = value
        self.src = src
        self.trg = trg
        self.lineno = lineno

