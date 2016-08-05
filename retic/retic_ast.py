import ast
from . import typing, exc
from .typing import retic_prefix, List

## AST nodes used by Reticulated, including Reticulated's internal
## representation of types. 

retic_prefix('typing')

typing.nominal()


record = typing.Dict[str, 'Type']


## Internal representation of types

class Type: 
    def __getitem__(self, k:str)->'Type':
        raise KeyError(k)
    def bind(self)->'Type':
        return self

@typing.constructor_fields
class Module(Type):
    def __init__(self, exports:record):
        self.exports = exports
    def __eq__(self, other):
        return isinstance(other, Module) and self.exports == other.exports
    def __getitem__(self, k:str)->Type:
        return self.exports[k]
    def to_ast(self, lineno:int, col_offset:int)->ast.expr:
        return ast.Name(id='object', ctx=ast.Load(), lineno=lineno, col_offset=col_offset)
    def __str__(self)->str:
        return 'Module'
    __repr__ = __str__


@typing.fields({'name':str, 'inherits':typing.List[Type], 'members':record, 'fields':record, 'initialized':bool})
class Class(Type):
    def __init__(self, name:str):
        self.name = name
        self.inherits = []
        self.members = {}
        self.fields = {}
        self.initialized = False
    def __eq__(self, other):
        return other is self

    def try_to_initialize(self):
        if all(isinstance(base, retic_ast.Dyn) or (isinstance(base, retic_ast.Class) and base.initialized) for base in self.parents):
            self.initialized = True

    def __getitem__(self, k:str):
        try:
            return self.get_class_member(k)
        except KeyError:
            if self.initialized:
                raise
            else:
                return Bot()
    def get_class_member(self, k:str):
        try:
            return self.members[k]
        except KeyError:
            for parent in self.inherits:
                try:
                    return parent.get_class_member(k)
                except KeyError:
                    pass
            return {
                '__init__': Function(PosAT([Dyn()]), Void())
            }[k]
    def get_instance_field(self, k:str):
        try:
            return self.fields[k]
        except KeyError:
            for parent in self.inherits:
                try:
                    return parent.get_instance_field(k)
                except KeyError:
                    pass
            raise KeyError

    def subtype_of(self, other:'Class'):
        return other is self or \
            any(sup.subtype_of(other) for sup in self.inherits)

    def to_ast(self, lineno:int, col_offset:int)->ast.expr:
        from .check_compiler import classname_marker
        return ast_trans.Call(func=ast.Name(id=classname_marker, ctx=ast.Load(), lineno=lineno, col_offset=col_offset),
                              args=[ast.Name(id=self.name, ctx=ast.Load(), lineno=lineno, col_offset=col_offset)], keywords=[],
                              starargs=None, kwargs=None, lineno=lineno, col_offset=col_offset)

    def __str__(self)->str:
        return 'Type[{}]'.format(self.name)
    __repr__ = __str__


@typing.constructor_fields
class Instance(Type):
    def __init__(self, instanceof:Class):
        self.instanceof = instanceof
    def __eq__(self, other):
        return isinstance(other, Instance) and self.instanceof == other.instanceof
    def __getitem__(self, k:str):
        try:
            return self.instanceof.get_instance_field(k)
        except KeyError:
            return self.instanceof[k].bind()
    def to_ast(self, lineno:int, col_offset:int)->ast.expr:
        return ast.Name(id=self.instanceof.name, ctx=ast.Load(), lineno=lineno, col_offset=col_offset)
    def __str__(self)->str:
        return self.instanceof.name
    __repr__ = __str__

class Bot(Type):
    def to_ast(self, lineno:int, col_offset:int)->ast.expr:
        raise exc.InternalReticulatedError()
    def __eq__(self, other):
        return isinstance(other, Bot)
    def __getitem__(self, k:str)->Type:
        return Bot()
    def get_instance_field(self, k:str):
        return Bot()

class Dyn(Type): 
    def to_ast(self, lineno:int, col_offset:int)->ast.expr:
        return ast.Name(id='object', ctx=ast.Load(), lineno=lineno, col_offset=col_offset)
    def __str__(self)->str:
        return 'Any'
    __repr__ = __str__
    def __eq__(self, other):
        return isinstance(other, Dyn)
    def __getitem__(self, k:str)->Type:
        return Dyn()
    def get_instance_field(self, k:str): 
        return Dyn()

class Union(Type):
    def __init__(self, alternatives:List(Type)):
        assert len(alternatives) >= 2
        self.alternatives = alternatives
    def __str__(self):
        return 'Union{}'.format(self.alternatives)
    def __eq__(self, other):
        return isinstance(other, Union) and self.alternatives == other.alternatives
    __repr__ = __str__
    def __getitem__(self, k:str)->Type:
        types = []
        for alt in alternatives:
            if alt[k] not in types:
                types.append(alt[k])
        if len(types) <= 1:
            return types[0]
        else:
            return Union(types)

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
    def __getitem__(self, k):
        s2s = Function(PosAT([]), Str())
        s2b = Function(PosAT([]), Bool())
        return {
            'capitalize': s2s,
            'casefold': s2s,
            'center': Function(ArbAT(), Str()), # int x str?
            'count': Function(PosAT([Str()]), Int()),
            'encode': Function(ArbAT(), Str()), # str x str?
            'endswith': Function(ArbAT(), Bool()), # str x int?
            'expandtabs': Function(PosAT([Int()]), Str()),
            'find': Function(ArbAT(), Int()), # ??
            'format': Function(ArbAT(), Str()), # ??
            'format_map': Function(PosAT([Dyn()]), Str()),
            'index': Function(PosAT([Str()]), Int()),
            'isalnum': s2b,
            'isalpha': s2b,
            'isdecimal': s2b,
            'isdigit': s2b,
            'isidentifier': s2b,
            'islower': s2b,
            'isnumeric': s2b,
            'isprintable': s2b,
            'isspace': s2b,
            'istitle': s2b,
            'isupper': s2b,
            'join': Function(PosAT([HTuple(Str())]), Str()),
            'ljust': Function(ArbAT(), Str()), # int x str?
            'lower': s2s,
            'lstrip': Function(ArbAT(), Str()), # str?
            'maketrans': Function(ArbAT(), Dyn()), # ??
            'partition': Function(PosAT([Str()]), HTuple(Str())),
            'replace': Function(ArbAT(), Str()), # str * str * int?
            'rfind': Function(ArbAT(), Int()), # ??
            'rindex': Function(PosAT([Str()]), Int()),
            'rjust': Function(ArbAT(), Str()), # int x str?
            'rpartition': Function(PosAT([Str()]), HTuple(Str())),
            'rsplit': Function(ArbAT(), List(Str())), # str?
            'rstrip': Function(ArbAT(), Str()), # str?
            'split': Function(ArbAT(), List(Str())), # str?
            'splitlines': Function(ArbAT(), List(Str())), # int?
            'startswith': Function(ArbAT(), Bool()), # str x int?
            'strip': Function(ArbAT(), Str()), # str?
            'swapcase': s2s,
            'title': s2s,
            'upper': s2s,
            'zfill': Function(PosAT([Int()]), Str())
        }[k]

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
        return 'Callable[{},{}]'.format(self.froms, self.to)
    __repr__ = __str__

    def __eq__(self, other):
        return isinstance(other, Function) and \
            self.froms == other.froms and self.to == other.to
    def bind(self)->Type:
        return Function(self.froms.bind(), self.to)

@typing.constructor_fields
class List(Type):
    def __init__(self, elts: Type):
        self.elts = elts

    def __getitem__(self, k):
        return {
            'append': Function(PosAT([self.elts]), Void()),
            'clear': Function(PosAT([]), Void()),
            'copy': Function(PosAT([]), List(self.elts)),
            'count': Function(PosAT([self.elts]), Int()),
            'extend': Function(PosAT([self.elts]), List(self.elts)),
            'index': Function(PosAT([self.elts]), Int()),
            'insert': Function(PosAT([Int(), self.elts]), Int()),
            'pop': Function(PosAT([]), self.elts),
            'remove': Function(PosAT([self.elts]), Void()),
            'reverse': Function(PosAT([]), Void()),
            'sort': Function(ArbAT(), Void())
        }[k]

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
        
    def bind(self):
        raise Exception('abstract')


# Essentially Dyn for argtypes: accepts anything
class ArbAT(ArgTypes):
    def __str__(self)->str:
        return '...'
    __repr__ = __str__
    def __eq__(self, other):
        return isinstance(other, ArbAT)
    def bind(self):
        return self

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
    def bind(self):
        assert len(self.types) >= 1
        return PosAT(self.types[1:])


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
    def bind(self):
        assert len(self.bindings) >= 1
        return NamedAT(self.bindings[1:])

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
    def bind(self):
        if len(self.bindings) >= 1:
            return NamedAT(self.bindings[1:])
        else:
            return NamedAT([])

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
