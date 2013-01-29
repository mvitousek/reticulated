import inspect
import ast
from decorator import decorator
from exceptions import UnknownTypeError

@decorator
def typed(fn, *args):
    argspec = inspect.getfullargspec(fn)
    for i in range(len(argspec.args)):
        p = argspec.args[i]
        if p in argspec.annotations:
            assert(has_type(args[i], argspec.annotations[p]))
    ret = fn(*args)
    if 'return' in argspec.annotations:
        assert has_type(ret, argspec.annotations['return']), 'Invalid return value'
    return ret

class Typed(type):
    def __init__(cls, *args):
        for name, m in inspect.getmembers(cls, inspect.isfunction):
            setattr(cls, name, typed(m))

class TypedObject(object, metaclass=Typed):
    pass

def typed_class(cls):
    for name, m in inspect.getmembers(cls, inspect.isfunction):
        setattr(cls, name, typed(m))
    return cls

class Fixed(object):
    def __call__(self):
        return self
class PyType(object):
    def __eq__(self, other):
        return (self.__class__ == other.__class__ or 
                (hasattr(self, 'builtin') and self.builtin == other))
    def to_ast(self):
        return ast.Name(id=self.__class__.__name__, ctx=ast.Load())
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
    def __init__(self, froms, to):
        self.froms = froms
        self.to = to
    def __eq__(self, other):
        return (super().__eq__(other) and  
                all(map(lambda p: p[0] == p[1], zip(self.froms, other.froms))) and
                self.to == other.to)
    def to_ast(self):
        return ast.Call(func=super().to_ast(), args=[ast.List(elts=map(lambda x:x.to_ast(), self.froms), 
                                                              ctx=Load()), self.to.to_ast()], 
                        keywords=[], starargs=None, kwargs=None)
class List(PyType):
    def __init__(self, type):
        self.type = type
    def __eq__(self, other):
        return super().__eq__(other) and self.type == other.type
    def to_ast(self):
        return ast.Call(func=super().to_ast(), args=[self.type.to_ast()], 
                        keywords=[], starargs=None, kwargs=None)
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
class Tuple(PyType):
    def __init__(self, *elements):
        self.elements = elements
    def __eq__(self, other):
        return super().__eq__(other) and len(self.elements) == len(other.elements) and \
            all(map(lambda p: p[0] == p[1], zip(self.elements, other.elements)))
    def to_ast(self):
        return ast.Call(func=super().to_ast(), args=list(map(lambda x:x.to_ast(), self.elements)),
                        keywords=[], starargs=None, kwargs=None)
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
class Class(PyType):
    def __init__(self, klass):
        self.klass = klass
    def __eq__(self, other):
        return super().__eq__(other) and self.klass == other.klass
    def to_ast(self):
        return ast.Call(func=super().to_ast(), args=[ast.Name(id=self.klass.__name__, ctx=ast.Load())], 
                        keywords=[], starargs=None, kwargs=None)
class ClassStatic(PyType):
    def __init__(self, klass_name):
        self.klass_name = klass_name
    def __eq__(self, other):
        return (super().__eq__(other) and self.klass_name == other.klass_name)
    def to_ast(self):
        return ast.Call(func=ast.Name(id=Class.__name__, ctx=ast.Load()), args=[ast.Name(id=self.klass_name, ctx=ast.Load())], 
                        keywords=[], starargs=None, kwargs=None)
class Instance(PyType):
    def __init__(self, klass):
        self.klass = klass
    def __eq__(self, other):
        return (super().__eq__(other) and self.klass == other.klass) or \
            self.klass == other
    def to_ast(self):
        return ast.Call(func=super().to_ast(), args=[ast.Name(id=self.klass.__name__, ctx=ast.Load())], 
                        keywords=[], starargs=None, kwargs=None)
class InstanceStatic(PyType):
    def __init__(self, klass_name):
        self.klass_name = klass_name
    def __eq__(self, other):
        return super().__eq__(other) and self.klass_name == other.klass_name
    def to_ast(self):
        return ast.Call(func=ast.Name(id=Class.__name__, ctx=ast.Load()), args=[ast.Name(id=self.klass_name, ctx=ast.Load())], 
                        keywords=[], starargs=None, kwargs=None)

Void = Void()
Dyn = Dyn()
Int = Int()
Float = Float()
Complex = Complex()
String = String()
Bool = Bool()

UNCALLABLES = [Void, Int, Float, Complex, String, Bool, Dict, List, Tuple]

@typed
def tycompat(ty1, ty2) -> bool:
    ty1 = normalize(ty1)
    ty2 = normalize(ty2)
    if tyinstance(ty1, Dyn) or tyinstance(ty2, Dyn):
        return True
    elif tyinstance(ty1, Object) or isinstance(ty1, dict):
        if tyinstance(ty1, Object):
            this = ty1.members
        else:
            this = ty1
        if tyinstance(ty2, Object):
            other = ty2.members
        elif isinstance(ty2, dict):
            other = ty2
        else: return False
        for k in this:
            if k in other and not tycompat(this[k], other[k]):
                return False
        return True
    elif tyinstance(ty1, Class) and tyinstance(ty2, Class):
        #return issubclass(ty1.klass, ty2.klass) or issubclass(ty2.klass, ty1.klass)
        raise UnexpectedTypeError('dynamic class in static check')
    elif tyinstance(ty1, ClassStatic) and tyinstance(ty2, ClassStatic):
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
    elif (tyinstance(ty1, Object) and tyinstance(ty2, InstanceStatic)) or \
            (tyinstance(ty2, InstanceStatic) and tyinstance(ty2, Object)):
        return True
    elif (tyinstance(ty1, Object) and tyinstance(ty2, ClassStatic)) or \
            (tyinstance(ty2, ClassStatic) and tyinstance(ty2, Object)):
        return True
    elif any(map(lambda x: tyinstance(ty1, x) and tyinstance(ty2, x), [Int, Float, Complex, String, Bool, Void])):
        return True
    elif tyinstance(ty1, InstanceStatic) and tyinstance(ty2, InstanceStatic):
        return True
    else: return False

@typed
def normalize(ty)->Instance(PyType):
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
    else: raise UnknownTypeError()

def tyinstance(ty, tyclass) -> bool:
    return (not inspect.isclass(tyclass) and ty == tyclass) or \
        (inspect.isclass(tyclass) and isinstance(ty, tyclass))

def func_has_type(argspec:inspect.FullArgSpec, ty) -> bool:
    arglen = len(argspec.args)
    for i in range(len(ty.froms)):
        frm = ty.froms[i]
        if i < arglen:
            p = argspec.args[i]
            if p in argspec.annotations and \
                    not tyinstance(argspec.annotations[p], frm):
                return False
        elif not argspec.varargs:
            return False
    if 'return' in argspec.annotations:
        return tyinstance(argspec.annotations['return'], ty.to)
    else:
        return True

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
        return (isinstance(val, list) or isinstance(val, tuple)) and \
            all(map(lambda x: has_type(x, ty.type), val))
    elif tyinstance(ty, Dict):
        return isinstance(val, dict) and \
            all(map(lambda x: has_type(x, ty.keys), val.keys())) and \
            all(map(lambda x: has_type(x, ty.values), val.values()))
    elif tyinstance(ty, Tuple):
        return (isinstance(val, tuple) or isinstance(val, list)) \
            and len(ty.elements) == len(val) and \
            all(map(lambda p: has_type(p[0], p[1]), zip(val, ty.elements)))
    elif tyinstance(ty, Class):
        return ty.klass == val
    elif tyinstance(ty, Object):
        for k in ty.members:
            if not hasattr(val, k) or not has_type(getattr(val, k), ty.members[k]):
                return False
        return True
    elif tyinstance(ty, Instance):
        return isinstance(val, ty.klass)
    elif inspect.isclass(ty):
        return isinstance(val, ty)
    elif isinstance(ty, dict):
        for k in ty:
            if not hasattr(val, k) or not has_type(getattr(val, k), ty[k]):
                return False
        return True
    else: raise UnknownTypeError('Unknown type ', ty)

def tyjoin(types):
    types = list(map(normalize, types))
    join = types[0]
    if tyinstance(join, Dyn):
        return Dyn
    for ty in types[1:]:
        if not tyinstance(ty, normalize(join).__class__) or \
                tyinstance(ty, Dyn):
            return Dyn
        elif tyinstance(ty, ClassStatic) or tyinstance(ty, InstanceStatic):
            join = join if ty.klass_name == join.klass_name else Dyn
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
        elif tyinstance(ty, Object):
            members = {}
            for x in ty.members:
                if x in join.members:
                    members[x] = tyjoin([ty.members[x], join.members[x]])
            join = Object(members)
        
        if join == Dyn: return Dyn
    return join
                

#@typed
#def atype(val):
#    try:
#        spec = inspect.getfullargspec(val)
#        argtys = []
#        for arg in spec.args:
#            if arg in spec.annotations:
#                argtys.append(normalize(spec.annotations[arg]))
#            else: argtys.append(Dyn)
#        if 'return' in spec.annotations:
#            to = spec.annotations['return']
#        else: to = Dyn
#        return Function(argtys, to)
#    except TypeError:
#        if isinstance(val, list):
            
