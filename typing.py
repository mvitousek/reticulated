import inspect, ast
from exceptions import UnknownTypeError

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

# The below are some nominal-typey things, not sure how well they will work
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

# We want to be able to refer to base types without constructing them
Void = Void()
Dyn = Dyn()
Int = Int()
Float = Float()
Complex = Complex()
String = String()
Bool = Bool()

UNCALLABLES = [Void, Int, Float, Complex, String, Bool, Dict, List, Tuple]


# MODES:
# 0 == Cast-as-assertion
TYPE_MODE = 0

def cast(val, src, trg, msg):
    if TYPE_MODE == 0: # Cast-as-assertion
        assert has_type(val, trg), "%s at line %d" % (msg, inspect.currentframe().f_back.f_lineno)
        return val

def check(val, trg, msg):
    if TYPE_MODE == 0: # Cast-as-assertion
        assert has_type(val, trg), "%s at line %d" % (msg, inspect.getlineno(val))
        return val

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

def tyinstance(ty, tyclass) -> bool:
    return (not inspect.isclass(tyclass) and ty == tyclass) or \
        (inspect.isclass(tyclass) and isinstance(ty, tyclass))
