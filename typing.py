import inspect, ast, collections
from exceptions import UnknownTypeError, UnexpectedTypeError

# More types: Collection? Set? Bytes?

### Types
class Fixed(object):
    def __call__(self):
        return self
class PyType(object):
    def __eq__(self, other):
        return (self.__class__ == other.__class__ or 
                (hasattr(self, 'builtin') and self.builtin == other))
    def to_ast(self):
        return ast.Name(id=self.__class__.__name__, ctx=ast.Load())
    def __str__(self):
        return self.__class__.__name__
    def __repr__(self):
        return self.__str__()
class Void(PyType, Fixed):
    builtin = type(None)
class Dyn(PyType, Fixed):
    builtin = None
class Int(PyType, Fixed):
    builtin = int
class Float(PyType, Fixed):
    builtin = float
class Complex(PyType, Fixed):
    builtin = complex
class String(PyType, Fixed):
    builtin = str
class Bool(PyType, Fixed):
    builtin = bool
class Function(PyType):
    def __init__(self, froms, to, var=None, kw=None, kwfroms=None):
        self.froms = froms
        self.to = to
        self.var = var
        self.kw = kw
        self.kwfroms = kwfroms
    def __eq__(self, other):
        return (super().__eq__(other) and  
                all(map(lambda p: p[0] == p[1], zip(self.froms, other.froms))) and
                self.to == other.to)
    def to_ast(self):
        return ast.Call(func=super().to_ast(), args=[ast.List(elts=[x.to_ast() for x in self.froms], 
                                                              ctx=ast.Load()), self.to.to_ast()], 
                        keywords=[], starargs=None, kwargs=None)
    def __str__(self):
        return 'Function([%s], %s)' % (','.join(str(elt) for elt in self.froms), self.to)
    def structural(self):
        return Object({key: Dyn for key in ['__annotations__', '__call__', '__class__', 
                                            '__closure__', '__code__', '__defaults__', 
                                            '__delattr__', '__dict__', '__doc__', '__eq__', 
                                            '__format__', '__ge__', '__get__', '__getattribute__', 
                                            '__globals__', '__gt__', '__hash__', '__init__', 
                                            '__kwdefaults__', '__le__', '__lt__', '__module__', 
                                            '__name__', '__ne__', '__new__', '__reduce__', 
                                            '__reduce_ex__', '__repr__', '__setattr__', 
                                            '__sizeof__', '__str__', '__subclasshook__']})

class List(PyType):
    def __init__(self, type):
        self.type = type
    def __eq__(self, other):
        return super().__eq__(other) and self.type == other.type
    def to_ast(self):
        return ast.Call(func=super().to_ast(), args=[self.type.to_ast()], 
                        keywords=[], starargs=None, kwargs=None)
    def __str__(self):
        return 'List(%s)' % self.type
    def structural(self):
        obj = {key: Dyn for key in ['__add__', '__class__', '__contains__', '__delattr__', 
                                    '__delitem__', '__doc__', '__eq__', '__format__', '__ge__', 
                                    '__getattribute__', '__getitem__', '__gt__', '__hash__', 
                                    '__iadd__', '__imul__', '__init__', '__iter__', '__le__', 
                                    '__len__', '__lt__', '__mul__', '__ne__', '__new__', 
                                    '__reduce__', '__reduce_ex__', '__repr__', '__reversed__', 
                                    '__rmul__', '__setattr__', '__setitem__', '__sizeof__', 
                                    '__str__', '__subclasshook__', 'append', 'count', 'extend', 
                                    'index', 'insert', 'pop', 'remove', 'reverse', 'sort']}
        obj['__setitem__'] = Function([Int, self.type], Void)
        obj['__getitem__'] = Function([Int], self.type)
        obj['append'] = Function([self.type], Void)
        obj['extend'] = Function([List(self.type)], Void)
        obj['index'] = Function([self.type], Int)
        obj['insert'] = Function([Int, self.type], Void)
        obj['pop'] = Function([], self.type)
        return obj
class Dict(PyType):
    def __init__(self, keys, values):
        self.keys = keys
        self.values = values
    def __eq__(self, other):
        return super().__eq__(other) and self.keys == other.keys and \
            self.values == other.values
    def to_ast(self):
        return ast.Call(func=super().to_ast(), args=[self.keys.to_ast(), self.values.to_ast()], 
                        keywords=[], starargs=None, kwargs=None)
    def __str__(self):
        return 'Dict(%s, %s)' % (self.keys, self.values)    
    def structural(self):
        obj = {key: Dyn for key in ['__class__', '__contains__', '__delattr__', 
                                    '__delitem__', '__doc__', '__eq__', '__format__', '__ge__', 
                                    '__getattribute__', '__getitem__', '__gt__', '__hash__', 
                                    '__init__', '__iter__', '__le__', 
                                    '__len__', '__lt__', '__ne__', '__new__', 
                                    '__reduce__', '__reduce_ex__', '__repr__', 
                                    '__setattr__', '__setitem__', '__sizeof__', 
                                    '__str__', '__subclasshook__', 'clear', 'copy', 'fromkeys', 
                                    'get', 'items', 'keys', 'pop', 'popitem', 'setdefault', 
                                    'update', 'values']}
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
class Tuple(PyType):
    def __init__(self, *elements):
        self.elements = elements
    def __eq__(self, other):
        return super().__eq__(other) and len(self.elements) == len(other.elements) and \
            all(map(lambda p: p[0] == p[1], zip(self.elements, other.elements)))
    def to_ast(self):
        return ast.Call(func=super().to_ast(), args=list(map(lambda x:x.to_ast(), self.elements)),
                        keywords=[], starargs=None, kwargs=None)
    def __str__(self):
        return 'Tuple(%s)' % (','.join([str(elt) for elt in self.elements]))
class Iterable(PyType):
    def __init__(self, type):
        self.type = type
    def __eq__(self, other):
        return super().__eq__(other) and self.type == other.type
    def to_ast(self):
        return ast.Call(func=super().to_ast(), args=[self.type.to_ast()], keywords=[],
                        starargs=None, kwargs=None)
    def __str__(self):
        return 'Iterable(%s)' % str(self.type)
class Set(PyType):
    def __init__(self, type):
        self.type = type
    def __eq__(self, other):
        return super().__eq__(other) and self.type == other.type
    def to_ast(self):
        return ast.Call(func=super().to_ast(), args=[self.type.to_ast()], keywords=[],
                        starargs=None, kwargs=None)
    def __str__(self):
        return 'Set(%s)' % str(self.type)
class Object(PyType):
    def __init__(self, members):
        self.members = members
    def __eq__(self, other):
        return (super().__eq__(other) and self.members == other.members) or \
            self.members == other
    def to_ast(self):
        return ast.Call(func=super().to_ast(), args=[ast.Dict(keys=list(map(lambda x: ast.Str(s=x), self.members.keys())),
                                                              values=list(map(lambda x: x.to_ast(), self.members.values())))],
                        keywords=[], starargs=None, kwargs=None)

class Parameter(object):
    def __init__(self, name, type, optional):
        self.name = name
        self.type = type
        self.optional = optional

# We want to be able to refer to base types without constructing them
Void = Void()
Dyn = Dyn()
Int = Int()
Float = Float()
Complex = Complex()
String = String()
Bool = Bool()

UNCALLABLES = [Void, Int, Float, Complex, String, Bool, Dict, List, Tuple, Set]

# Casts 
def retic_cas_cast(val, src, trg, msg):
    # Can't (easily) just call retic_cas_check because of frame introspection resulting in
    # incorrect line number reporting
    assert has_type(val, trg), "%s at line %d" % (msg, inspect.currentframe().f_back.f_lineno)
    return val

def retic_cas_check(val, trg, msg):
    assert has_type(val, trg), "%s at line %d" % (msg, inspect.currentframe().f_back.f_lineno)
    return val

def retic_error(msg):
    assert False, "%s at line %d" % (msg, inspect.currentframe().f_back.f_lineno)

# Utilities

def has_type(val, ty) -> bool:
    if tyinstance(ty, Dyn):
        return True
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
            spec = inspect.getfullargspec(val)
            new_spec = inspect.FullArgSpec(spec.args[1:], spec.varargs, spec.varkw, 
                                           spec.defaults, spec.kwonlyargs, 
                                           spec.kwonlydefaults, spec.annotations)
            return func_has_type(new_spec, ty)
        elif inspect.isfunction(val): # Normal function
            return func_has_type(inspect.getfullargspec(val), ty)
        elif inspect.isclass(val): 
            if inspect.isfunction(val.__init__):
                spec = inspect.getfullargspec(val.__init__)
                new_spec = inspect.FullArgSpec(spec.args[1:], spec.varargs, spec.varkw, 
                                               spec.defaults, spec.kwonlyargs, 
                                               spec.kwonlydefaults, spec.annotations)
                return func_has_type(new_spec, ty)
            else: return True
        elif inspect.isbuiltin(val):
            return True
        elif hasattr(val, '__call__'):
            spec = inspect.getfullargspec(val.__call__)
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
    elif tyinstance(ty, Object):
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

def func_has_type(argspec:inspect.FullArgSpec, ty) -> bool:
    arglen = len(argspec.args)
    for i in range(len(ty.froms)):
        frm = ty.froms[i]
        if i < arglen:
            p = argspec.args[i]
            if p in argspec.annotations and \
                    not tycompat(argspec.annotations[p], frm):
                return False
        elif not argspec.varargs:
            return False
    if len(ty.froms) < arglen:
        return False
    if 'return' in argspec.annotations:
        return tycompat(argspec.annotations['return'], ty.to)
    else:
        return True

def tyinstance(ty, tyclass) -> bool:
    return (not inspect.isclass(tyclass) and ty == tyclass) or \
        (inspect.isclass(tyclass) and isinstance(ty, tyclass))

def subcompat(ty1, ty2):
    if tyinstance(ty1, Object) and tyinstance(ty2, Object):
        for k in ty2.members:
            if k not in ty1.members or not subcompat(ty1.members[k], ty2.members[k]):
                return False
        return True
    elif tyinstance(ty1, List):
        if tyinstance(ty2, List):
            return subcompat(ty1.type, ty2.type)
        elif tyinstance(ty2, Object):
            return subcompat(ty1.structural(), ty2)
        elif tyinstance(ty2, Iterable):
            return subcompat(ty1.type, ty2.type)
        else: return False
    elif tyinstance(ty1, Set):
        if tyinstance(ty2, Set):
            return subcompat(ty1.type, ty2.type)
        elif tyinstance(ty2, Object):
            return subcompat(ty1.structural(), ty2)
        elif tyinstance(ty2, Iterable):
            return subcompat(ty1.type, ty2.type)
        else: return False
    elif tyinstance(ty1, Tuple):
        if tyinstance(ty2, Tuple):
            return len(ty1.elements)==len(ty2.elements) and \
                all(subcompat(t1e, t2e) for (t1e, t2e) in zip(ty1.elements, ty2.elements))
        elif tyinstance(ty2, Object):
            return subcompat(ty1.structural(), ty2)
        elif tyinstance(ty2, Iterable):
            return subcompat(ty1.type, ty2.type)
        else: return False
    elif tyinstance(ty1, Dict):
        if tyinstance(ty2, Dict):
            return subcompat(ty1.keys, ty2.keys) and subcompat(ty1.values, ty2.values)
        elif tyinstance(ty2, Object):
            return subcompat(ty1.structural(), ty2)
        elif tyinstance(ty2, Iterable):
            return subcompat(ty1.keys, ty2.type)
        else: return False
    elif tyinstance(ty1, Iterable):
        if tyinstance(ty2, Iterable):
            return subcompat(ty1.type, ty2.type)
        elif tyinstance(ty2, Object):
            return subcompat(ty1.structural(), ty2)
        else: return False
    else: return tycompat(ty1, ty2)

def tycompat(ty1, ty2) -> bool:
    if tyinstance(ty1, Dyn) or tyinstance(ty2, Dyn):
        return True
    elif tyinstance(ty1, Object):
        this = ty1.members
        if tyinstance(ty2, Object):
            other = ty2.members
        else: return False
        for k in this:
            if k in other and not tycompat(this[k], other[k]):
                return False
        return True
    elif tyinstance(ty1, Tuple):
        if tyinstance(ty2, Tuple):
            return len(ty1.elements) == len(ty2.elements) and \
                all(map(lambda p: tycompat(p[0], p[1]), zip(ty1.elements, ty2.elements)))
        elif tyinstance(ty2, List):
            return all(tycompat(a, ty2.type) for a in ty1.elements)
        else: return False
    elif tyinstance(ty1, List):
        if tyinstance(ty2, Tuple):
            return all(tycompat(a, ty1.type) for a in ty2.elements)
        elif tyinstance(ty2, List):
            return tycompat(ty1.type, ty2.type)
        else: return False
    elif tyinstance(ty1, Dict) and tyinstance(ty2, Dict):
        return tycompat(ty1.keys, ty2.keys) and tycompat(ty1.values, ty2.values)
    elif tyinstance(ty1, Function) and tyinstance(ty2, Function):
        return (len(ty1.froms) == len(ty2.froms) and 
                all(map(lambda p: tycompat(p[0], p[1]), zip(ty1.froms, ty2.froms))) and 
                tycompat(ty1.to, ty2.to))
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
        return Object(nty)
    elif tyinstance(ty, Object):
        nty = {}
        for k in ty.members:
            if type(k) != str:
                raise UnknownTypeError()
            nty[k] = normalize(ty.members[k])
        return Object(nty)
    elif tyinstance(ty, Tuple):
        return Tuple(*[normalize(t) for t in ty.elements])
    elif tyinstance(ty, Function):
        return Function([normalize(t) for t in ty.froms], normalize(ty.to))
    elif tyinstance(ty, Dict):
        return Dict(normalize(ty.keys), normalize(ty.values))
    elif tyinstance(ty, List):
        return List(normalize(ty.type))
    elif isinstance(ty, PyType):
        return ty
    else: raise UnknownTypeError(ty)
