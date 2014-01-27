import inspect, ast, collections, sys, flags
from exc import UnknownTypeError, UnexpectedTypeError

if flags.PY_VERSION == 2:
    class getfullargspec(object):
        def __init__(self, f):
            self.args, self.varargs, self.varkw, self.defaults = \
                inspect.getargspec(f)
            self.kwonlyargs = []
            self.kwonlydefaults = None
            if hasattr(f, '__annotations__'):
                self.annotations = f.__annotations__
            else:
                self.annotations = {}
        def __iter__(self):
            yield self.args
            yield self.varargs
            yield self.varkw
            yield self.defaults
elif flags.PY_VERSION == 3:
    from inspect import getfullargspec

### Python 2.7 annotation
def retic_typed(ty, error_function='retic_error'):
    def tyfn(fn):
        if tyinstance(ty, Function):
            spec = inspect.getargspec(fn)
            posargs = spec.args
            if len(posargs) != len(ty.froms):
                error_function('Mismatch in number of positional arguments')
            annotations = dict(zip(posargs, ty.froms))
            annotations['return'] = ty.to
            fn.__annotations__ = annotations
        else:
            error_function('Functions must be annotated with function types')
        return fn
    return tyfn

def is_annotation(dec):
    return isinstance(dec, ast.Call) and isinstance(dec.func, ast.Name) and \
        dec.func.id == 'retic_typed'

### Metaclass constructor for monotonic objects
def monotonic(metaclass):
    class Monotonic(metaclass):
        monotonic_capable_class = True
    return Monotonic
Monotonic = monotonic(type)

def warn(msg, priority):
    if flags.WARNINGS >= priority:
        print('WARNING:', msg)

### Types
class Fixed(object):
    def __call__(self):
        return self
    def substitute(self, var, ty):
        return self
class PyType(object):
    def __eq__(self, other):
        return (self.__class__ == other.__class__ or 
                (hasattr(self, 'builtin') and self.builtin == other))
    def to_ast(self):
        return ast.Name(id=self.__class__.__name__, ctx=ast.Load())
    def static(self):
        return True
    def __str__(self):
        return self.__class__.__name__
    def __repr__(self):
        return self.__str__()
class Void(PyType, Fixed):
    builtin = type(None)
class Bottom(PyType,Fixed):
    pass
class Dyn(PyType, Fixed):
    builtin = None
    def static(self):
        return False
class Int(PyType, Fixed):
    builtin = int
class Float(PyType, Fixed):
    builtin = float
class Complex(PyType, Fixed):
    builtin = complex
class String(PyType, Fixed):
    builtin = str
    def structure(self):
        obj = Record({key: Dyn for key in dir('Hello World')})
        return obj
class Bool(PyType, Fixed):
    builtin = bool
    def structure(self):
        obj = Record({key: Dyn for key in dir(True)})
        return obj
class Function(PyType):
    def __init__(self, froms, to, var=None, kw=None, kwfroms=None):
        self.froms = froms
        self.to = to
        self.var = var
        self.kw = kw
        self.kwfroms = kwfroms
    def __eq__(self, other):
        return (super(Function, self).__eq__(other) and  
                all(map(lambda p: p[0] == p[1], zip(self.froms, other.froms))) and
                self.to == other.to)
    def static(self):
        return all([f.static() for f in self.froms]) and \
            self.to.static()
    def to_ast(self):
        return ast.Call(func=super(Function, self).to_ast(), args=[ast.List(elts=[x.to_ast() for x in self.froms], 
                                                              ctx=ast.Load()), self.to.to_ast()], 
                        keywords=[], starargs=None, kwargs=None)
    def __str__(self):
        return 'Function([%s], %s)' % (','.join(str(elt) for elt in self.froms), self.to)
    def structure(self):
        return Record({key: Dyn for key in dir(lambda x: None)})
    def substitute(self, var, ty):
        self.froms = [f.substitute(var, ty) for f in self.froms]
        self.to = self.to.substitute(var, ty)
        return self
class List(PyType):
    def __init__(self, type):
        self.type = type
    def __eq__(self, other):
        return super(List, self).__eq__(other) and self.type == other.type
    def static(self):
        return self.type.static()
    def to_ast(self):
        return ast.Call(func=super(List, self).to_ast(), args=[self.type.to_ast()], 
                        keywords=[], starargs=None, kwargs=None)
    def __str__(self):
        return 'List(%s)' % self.type
    def structure(self):
        obj = {key: Dyn for key in dir([])}
        obj['__setitem__'] = Function([Int, self.type], Void)
        obj['__getitem__'] = Function([Int], self.type)
        obj['append'] = Function([self.type], Void)
        obj['extend'] = Function([List(self.type)], Void)
        obj['index'] = Function([self.type], Int)
        obj['insert'] = Function([Int, self.type], Void)
        obj['pop'] = Function([], self.type)
        return obj
    def substitute(self, var, ty):
        self.type = self.type.substitute(var, ty)
        return self
class Dict(PyType):
    def __init__(self, keys, values):
        self.keys = keys
        self.values = values
    def __eq__(self, other):
        return super(Dict, self).__eq__(other) and self.keys == other.keys and \
            self.values == other.values
    def static(self):
        return self.keys.static() and self.values.static()
    def to_ast(self):
        return ast.Call(func=super(Dict, self).to_ast(), args=[self.keys.to_ast(), self.values.to_ast()], 
                        keywords=[], starargs=None, kwargs=None)
    def __str__(self):
        return 'Dict(%s, %s)' % (self.keys, self.values)    
    def structure(self):
        obj = {key: Dyn for key in dir({})}
        obj['__setitem__'] = Function([self.keys, self.values], Void)
        obj['__getitem__'] = Function([self.keys], self.values)
        obj['copy'] = Function([], Dict(self.keys, self.values))
        obj['get'] = Function([self.keys], self.values)
        obj['items'] = Function([], Iterable(Tuple(self.keys, self.values)))
        obj['keys'] = Function([], Iterable(self.keys))
        obj['pop'] = Function([self.keys], self.values)
        obj['popitem'] = Function([], Tuple(self.keys,self.values))
        obj['update'] = Function([Dict(self.keys, self.values)], Void)
        obj['values'] = Function([], Iterable(self.values))
        return obj
    def substitute(self, var, ty):
        self.keys = self.keys.substitute(var, ty)
        self.values = self.values.substitute(var, ty)
        return self
class Tuple(PyType):
    def __init__(self, *elements):
        self.elements = elements
    def __eq__(self, other):
        return super(Tuple, self).__eq__(other) and len(self.elements) == len(other.elements) and \
            all(map(lambda p: p[0] == p[1], zip(self.elements, other.elements)))
    def static(self):
        return all([e.static() for e in self.elements])
    def to_ast(self):
        return ast.Call(func=super(Tuple, self).to_ast(), args=list(map(lambda x:x.to_ast(), self.elements)),
                        keywords=[], starargs=None, kwargs=None)
    def __str__(self):
        return 'Tuple(%s)' % (','.join([str(elt) for elt in self.elements]))
    def structure(self):
        # Not yet defining specific types
        obj = {key: Dyn for key in dir(())}
        return obj
    def substitute(self, var, ty):
        self.elements = [e.substitute(var, ty) for e in self.elements]
        return self
class Iterable(PyType):
    def __init__(self, type):
        self.type = type
    def __eq__(self, other):
        return super(Iterable, self).__eq__(other) and self.type == other.type
    def static(self):
        return self.type.static()
    def to_ast(self):
        return ast.Call(func=super(Iterable, self).to_ast(), args=[self.type.to_ast()], keywords=[],
                        starargs=None, kwargs=None)
    def __str__(self):
        return 'Iterable(%s)' % str(self.type)
    def structure(self):
        # Not yet defining specific types
        return {'__iter__': Iterable(self.type)}
    def substitute(self, var, ty):
        self.type = self.type.substitute(var, ty)
        return self
class Set(PyType):
    def __init__(self, type):
        self.type = type
    def __eq__(self, other):
        return super(Set, self).__eq__(other) and self.type == other.type
    def static(self):
        return self.type.static()
    def to_ast(self):
        return ast.Call(func=super(Set, self).to_ast(), args=[self.type.to_ast()], keywords=[],
                        starargs=None, kwargs=None)
    def __str__(self):
        return 'Set(%s)' % str(self.type)
    def structure(self):
        # Not yet defining specific types
        obj = {key: Dyn for key in dir({1})}
        return obj
    def substitute(self, var, ty):
        self.type = self.type.substitute(var, ty)
        return self
class Record(PyType):
    def __init__(self, members):
        self.members = members
    def __eq__(self, other):
        return (super(Record, self).__eq__(other) and self.members == other.members) or \
            self.members == other
    def static(self):
        return all([m.static() for m in self.members.values()])
    def to_ast(self):
        return ast.Call(func=super(Record, self).to_ast(), 
                        args=[ast.Dict(keys=list(map(lambda x: ast.Str(s=x), self.members.keys())),
                                       values=list(map(lambda x: x.to_ast(), self.members.values())))],
                        keywords=[], starargs=None, kwargs=None)
    def __str__(self):
        return 'Record(%s)' % str(self.members)
    def substitute(self, var, ty):
        self.members = {k:self.members[k].substitute(var, ty) for k in self.members}
        return self

# We want to be able to refer to base types without constructing them
Void = Void()
Dyn = Dyn()
Int = Int()
Float = Float()
Complex = Complex()
String = String()
Bool = Bool()
Bottom = Bottom()

UNCALLABLES = [Void, Int, Float, Complex, String, Bool, Dict, List, Tuple, Set]

# Utilities

def has_type(val, ty):
    if tyinstance(ty, Dyn):
        return True
    if tyinstance(ty, Bottom):
        return False
    elif tyinstance(ty, Void):
        return val == None
    elif tyinstance(ty, Int):
        return isinstance(val, int)
    elif tyinstance(ty, Bool):
        return isinstance(val, bool)
    elif tyinstance(ty, Float):
        return isinstance(val, float)
    elif tyinstance(ty, Complex):
        return isinstance(val, complex)
    elif tyinstance(ty, String):
        return isinstance(val, str)
    elif tyinstance(ty, Function):
        if inspect.ismethod(val): # Only true for bound methods
            spec = getfullargspec(val)
            new_spec = inspect.FullArgSpec(spec.args[1:], spec.varargs, spec.varkw, 
                                           spec.defaults, spec.kwonlyargs, 
                                           spec.kwonlydefaults, spec.annotations)
            return func_has_type(new_spec, ty)
        elif inspect.isfunction(val): # Normal function
            return func_has_type(getfullargspec(val), ty)
        elif inspect.isclass(val): 
            if inspect.isfunction(val.__init__):
                spec = getfullargspec(val.__init__)
                new_spec = inspect.FullArgSpec(spec.args[1:], spec.varargs, spec.varkw, 
                                               spec.defaults, spec.kwonlyargs, 
                                               spec.kwonlydefaults, spec.annotations)
                return func_has_type(new_spec, ty)
            else: return True
        elif inspect.isbuiltin(val):
            return True
        elif hasattr(val, '__call__'):
            spec = getfullargspec(val.__call__)
            new_spec = inspect.FullArgSpec(spec.args[1:], spec.varargs, spec.varkw, 
                                           spec.defaults, spec.kwonlyargs, 
                                           spec.kwonlydefaults, spec.annotations)
            return func_has_type(new_spec, ty)
        elif callable(val):
            return True # No fucking clue
        else: return False
    elif tyinstance(ty, List):
        return (isinstance(val, list)) and \
            all(map(lambda x: has_type(x, ty.type), val))
    elif tyinstance(ty, Set):
        return isinstance(val, set) and \
            all(map(lambda x: has_type(x, ty.type), val))
    elif tyinstance(ty, Dict):
        return isinstance(val, dict) and \
            all(map(lambda x: has_type(x, ty.keys), val.keys())) and \
            all(map(lambda x: has_type(x, ty.values), val.values()))
    elif tyinstance(ty, Tuple):
        return (isinstance(val, tuple)) \
            and len(ty.elements) == len(val) and \
            all(map(lambda p: has_type(p[0], p[1]), zip(val, ty.elements)))
    elif tyinstance(ty, Iterable):
        if (isinstance(val, tuple) or isinstance(val, list) or isinstance(val, set)) or iter(val) is not val:
            return all(map(lambda x: has_type(x, ty.type), val))
        elif isinstance(val, collections.Iterable):
            if hasattr(val, '__iter__'):
                return has_type(val.__iter__, Function([Dyn], Iterable(ty.type)))
            else: return True
        else: return False
    elif tyinstance(ty, Record):
        for k in ty.members:
            if not hasattr(val, k) or not has_type(getattr(val, k), ty.members[k]):
                return False
        return True
    elif isinstance(ty, dict):
        for k in ty:
            if not hasattr(val, k) or not has_type(getattr(val, k), ty[k]):
                return False
        return True
    else: raise UnknownTypeError('Unknown type ', ty)

def func_has_type(argspec, ty):
    arglen = len(argspec.args)
    for i in range(len(ty.froms)):
        frm = ty.froms[i]
        if i < arglen:
            p = argspec.args[i]
            if p in argspec.annotations and \
                    not subcompat(frm, argspec.annotations[p]):
                return False
        elif not argspec.varargs:
            return False
    if len(ty.froms) < arglen:
        return False
    if 'return' in argspec.annotations:
        return subcompat(argspec.annotations['return'], ty.to)
    else:
        return True

def tyinstance(ty, tyclass):
    return (not inspect.isclass(tyclass) and ty == tyclass) or \
        (inspect.isclass(tyclass) and isinstance(ty, tyclass))

def subcompat(ty1, ty2):
    if tyinstance(ty1, Record) and tyinstance(ty2, Record):
        for k in ty2.members:
            if k not in ty1.members or not subcompat(ty1.members[k], ty2.members[k]):
                return False
        return True
    elif tyinstance(ty1, List):
        if tyinstance(ty2, List):
            return subcompat(ty1.type, ty2.type)
        elif tyinstance(ty2, Record):
            return subcompat(ty1.structure(), ty2)
        elif tyinstance(ty2, Iterable):
            return subcompat(ty1.type, ty2.type)
        else: return tycompat(ty1, ty2)
    elif tyinstance(ty1, String):
        if tyinstance(ty2, Record):
            return subcompat(ty1.structure(), ty2)
        elif tyinstance(ty2, Iterable):
            return subcompat(String, ty2.type)
        else: return tycompat(ty1, ty2)
    elif tyinstance(ty1, Set):
        if tyinstance(ty2, Set):
            return subcompat(ty1.type, ty2.type)
        elif tyinstance(ty2, Record):
            return subcompat(ty1.structure(), ty2)
        elif tyinstance(ty2, Iterable):
            return subcompat(ty1.type, ty2.type)
        else: return tycompat(ty1, ty2)
    elif tyinstance(ty1, Tuple):
        if tyinstance(ty2, Tuple):
            return len(ty1.elements)==len(ty2.elements) and \
                all(subcompat(t1e, t2e) for (t1e, t2e) in zip(ty1.elements, ty2.elements))
        elif tyinstance(ty2, Record):
            return subcompat(ty1.structure(), ty2)
        elif tyinstance(ty2, Iterable):
            join = tyjoin(ty1.elements)
            return subcompat(join, ty2.type)
        else: return tycompat(ty1, ty2)
    elif tyinstance(ty1, Dict):
        if tyinstance(ty2, Dict):
            return subcompat(ty1.keys, ty2.keys) and subcompat(ty1.values, ty2.values)
        elif tyinstance(ty2, Record):
            return subcompat(ty1.structure(), ty2)
        elif tyinstance(ty2, Iterable):
            return subcompat(ty1.keys, ty2.type)
        else: return tycompat(ty1, ty2)
    elif tyinstance(ty1, Iterable):
        if tyinstance(ty2, Iterable):
            return subcompat(ty1.type, ty2.type)
        elif tyinstance(ty2, Record):
            return subcompat(ty1.structure(), ty2)
        else: return tycompat(ty1, ty2)
    elif tyinstance(ty1, Bool):
        if tyinstance(ty2, Record):
            return subcompat(ty1.structure(), ty2)
        else: return tycompat(ty1, ty2)
    elif tyinstance(ty1, Function):
        if tyinstance(ty2, Function):
            return (len(ty1.froms) == len(ty2.froms) and 
                    all(map(lambda p: subcompat(p[0], p[1]), zip(ty2.froms, ty1.froms))) and 
                    subcompat(ty1.to, ty2.to))
        elif tyinstance(ty2, Record):
            return subcompat(ty1.structure(), ty2)
        else: return tycompat(ty1, ty2)
    else: return tycompat(ty1, ty2)

def tycompat(ty1, ty2):
    if tyinstance(ty1, Dyn) or tyinstance(ty2, Dyn):
        return True
    elif tyinstance(ty1, Bottom) or tyinstance(ty2, Bottom):
        return True
    elif any(map(lambda x: tyinstance(ty1, x) and tyinstance(ty2, x), [Int, Float, Complex, String, Bool, Void])):
        return True
    else: return False

def normalize(ty):
    if ty == int:
        return Int
    elif ty == bool:
        return Bool
    elif ty == float:
        return Float
    elif ty == type(None):
        return Void
    elif ty == complex:
        return Complex
    elif ty == str:
        return String
    elif ty == None:
        return Dyn
    elif isinstance(ty, dict):
        nty = {}
        for k in ty:
            if type(k) != str:
                raise UnknownTypeError()
            nty[k] = normalize(ty[k])
        return Record(nty)
    elif tyinstance(ty, Record):
        nty = {}
        for k in ty.members:
            if type(k) != str:
                raise UnknownTypeError()
            nty[k] = normalize(ty.members[k])
        return Record(nty)
    elif tyinstance(ty, Tuple):
        return Tuple(*[normalize(t) for t in ty.elements])
    elif tyinstance(ty, Function):
        return Function([normalize(t) for t in ty.froms], normalize(ty.to))
    elif tyinstance(ty, Dict):
        return Dict(normalize(ty.keys), normalize(ty.values))
    elif tyinstance(ty, List):
        return List(normalize(ty.type))
    elif tyinstance(ty, Set):
        return Set(normalize(ty.type))
    elif tyinstance(ty, Iterable):
        return Iterable(normalize(ty.type))
    elif isinstance(ty, PyType):
        return ty
    else: raise UnknownTypeError(ty)

def tyjoin(types):
    if all(tyinstance(x, Bottom) for x in types):
        return Bottom
    types = [ty for ty in types if not tyinstance(ty, Bottom)]
    if len(types) == 0:
        return Dyn
    types = list(map(normalize, types))
    join = types[0]
    if tyinstance(join, Dyn):
        return Dyn
    for ty in types[1:]:
        if not tyinstance(ty, normalize(join).__class__) or \
                tyinstance(ty, Dyn):
            return Dyn
        elif tyinstance(ty, List):
            join = List(tyjoin([ty.type, join.type]))
        elif tyinstance(ty, Tuple):
            if len(ty.elements) == len(join.elements):
                join = Tuple(*[tyjoin(list(p)) for p in zip(ty.elements, join.elements)])
            else: return Dyn
        elif tyinstance(ty, Dict):
            join = Dict(tyjoin([ty.keys, join.keys]), tyjoin([ty.values, join.values]))
        elif tyinstance(ty, Function):
            if len(ty.froms) == len(join.froms):
                join = Function([tyjoin(list(p)) for p in zip(ty.froms, join.froms)], 
                                tyjoin([ty.to, join.to]))
            else: return Dyn
        elif tyinstance(ty, Record):
            members = {}
            for x in ty.members:
                if x in join.members:
                    members[x] = tyjoin([ty.members[x], join.members[x]])
            join = Record(members)
        
        if join == Dyn: return Dyn
    return join
