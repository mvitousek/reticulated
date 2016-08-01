import ast
from . import typing, exc
from .typing import retic_prefix

## AST nodes used by Reticulated, including Reticulated's internal
## representation of types. 

retic_prefix('typing')

typing.nominal()



## Internal representation of types

class Type: pass

class Bot(Type):
    def to_ast(self, lineno:int, col_offset:int)->ast.expr:
        raise exc.InternalReticulatedError()
    def __eq__(self, other):
        return isinstance(other, Bot)

class Dyn(Type): 
    def to_ast(self, lineno:int, col_offset:int)->ast.expr:
        return ast.Name(id='object', ctx=ast.Load(), lineno=lineno, col_offset=col_offset)
    def __str__(self)->str:
        return 'Any'
    __repr__ = __str__
    def __eq__(self, other):
        return isinstance(other, Dyn)

@typing.fields({'type': str})
class Primitive(Type): 
    def to_ast(self, lineno:int, col_offset:int)->ast.expr:
        return ast.Name(id=self.type, ctx=ast.Load(), lineno=lineno, col_offset=col_offset)
    def __str__(self)->str:
        return self.type
    __repr__ = __str__
    def __eq__(self, other):
        return isinstance(other, self.__class__)

class Int(Primitive):
    def __init__(self):
        self.type = 'int'

@typing.fields({'n': int})
class SingletonInt(Primitive):
    def __init__(self, n:int):
        self.n = n
        self.type = 'int'

class Float(Primitive):
    def __init__(self):
        self.type = 'float'

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
    __repr__ = __str__

    def __eq__(self, other):
        return isinstance(other, Function) and \
            self.froms == other.froms and self.to == other.to

@typing.constructor_fields
class List(Type):
    def __init__(self, elts: Type):
        self.elts = elts

    def to_ast(self, lineno:int, col_offset:int)->ast.expr:
        return ast.Name(id='list', ctx=ast.Load(), lineno=lineno, col_offset=col_offset)

    def __str__(self)->str:
        return 'List[{}]'.format(self.elts)
    __repr__ = __str__

    def __eq__(self, other):
        return isinstance(other, List) and \
            self.elts == other.elts

@typing.constructor_fields
class Tuple(Type):
    def __init__(self, *elts: typing.List[Type]):
        self.elts = elts

    def to_ast(self, lineno:int, col_offset:int)->ast.expr:
        return ast.Name(id='tuple', ctx=ast.Load(), lineno=lineno, col_offset=col_offset)

    def __str__(self)->str:
        return 'Tuple{}'.format(list(self.elts))
    __repr__ = __str__

    def __eq__(self, other):
        return isinstance(other, Tuple) and \
            self.elts == other.elts

@typing.constructor_fields
class HTuple(Type):
    def __init__(self, elts: Type):
        self.elts = elts

    def to_ast(self, lineno:int, col_offset:int)->ast.expr:
        return ast.Name(id='tuple', ctx=ast.Load(), lineno=lineno, col_offset=col_offset)

    def __str__(self)->str:
        return 'Tuple[{}, ...]'.format(self.elts)
    __repr__ = __str__

    def __eq__(self, other):
        return isinstance(other, HTuple) and \
            self.elts == other.elts

# ArgTypes is the LHS of the function type arrow. We should _not_ use
# this on the inside of functions to determine what the type env or
# required transient checks are.
class ArgTypes: 
    def match(self, nargs: int)->typing.List[Type]:
        raise Exception('abstract')

    def can_match(self, nargs: int)->bool:
        raise Exception('abstract')


# Essentially Dyn for argtypes: accepts anything
class ArbAT(ArgTypes):
    def __str__(self)->str:
        return '...'
    __repr__ = __str__
    def __eq__(self, other):
        return isinstance(other, ArbAT)

# Strict positional type: can't be called with anything but 
# the arguments specified
@typing.constructor_fields
class PosAT(ArgTypes):
    def __init__(self, types: typing.List[Type]):
        self.types = types

    def __str__(self)->str:
        return str(self.types)
    __repr__ = __str__
    def __eq__(self, other):
        return isinstance(other, PosAT) and \
            self.types == other.types


# Strict named positional type
@typing.constructor_fields
class NamedAT(ArgTypes):
    def __init__(self, bindings: typing.List[typing.Tuple[str, Type]]):
        self.bindings = bindings

    def __str__(self)->str:
        return str(['{}: {}'.format(k, v) for k, v in self.bindings])
    __repr__ = __str__
    def __eq__(self, other):
        return isinstance(other, NamedAT) and \
            self.bindings == other.bindings

# Permissive named positional type: will reject positional arguments known
# to be wrong, but if called with varargs, kwargs, etc, will give up
@typing.constructor_fields
class ApproxNamedAT(ArgTypes):
    def __init__(self, bindings: typing.List[typing.Tuple[str, Type]]):
        self.bindings = bindings

    def __str__(self)->str:
        return str(['{}: {}'.format(k, v) for k, v in self.bindings] + ['...'])
    __repr__ = __str__
    def __eq__(self, other):
        return isinstance(other, ApproxNamedAT) and \
            self.bindings == other.bindings

# Intermediate psuedo-Python AST expressions
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
class ExpandSeq(ast.expr):
    def __init__(self, body:typing.List[ast.stmt], lineno:int, col_offset:int):
        self.body = body
        self.lineno = lineno
        self.col_offset = col_offset
