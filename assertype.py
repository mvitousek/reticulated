import inspect
from decorator import decorator

@decorator
def typed(fn, *args):
    argspec = inspect.getfullargspec(fn)
    for i in range(len(argspec.args)):
        p = argspec.args[i]
        if p in argspec.annotations:
            assert(has_type(args[i], argspec.annotations[p]))
    ret = fn(*args)
    if 'return' in argspec.annotations:
        assert(isinstance(ret, argspec.annotations['return']))
    return ret

class PyType(object):
    pass
class Dyn(PyType):
    builtin = None
class Int(PyType):
    builtin = int
class Float(PyType):
    builtin = float
class Complex(PyType):
    builtin = complex
class String(PyType):
    builtin = str
class Bool(PyType):
    builtin = bool
class Function(PyType):
    def __init__(self, froms, to):
        self.froms = froms
        self.to = to
class List(PyType):
    def __init__(self, type):
        self.type = type
class Dict(PyType):
    def __init__(self, keys, values):
        self.keys = keys
        self.values = values
class Tuple(PyType):
    def __init__(self, *elements):
        self.elements = elements
class Class(PyType):
    def __init__(self, members=None, klass=None):
        if members == None and klass == None:
            raise TypeError('A class type must be constructed with either a members or klass argument')
        if members != None and klass != None:
            raise TypeError('A class type must be constructed with only one of a members or a klass argument')
        if members != None:
            self.members = members
        else:
            # Get the members of the class
            pass
class Object(PyType):
    def __init__(self, members=None, obj=None):
        if members == None and obj == None:
            raise TypeError('An object type must be constructed with either a members or obj argument')
        if members != None and obj != None:
            raise TypeError('An object type must be constructed with only one of a members and a obj argument')
        if members != None:
            self.members = members
        else:
            # Get the members of the object
            pass
class Instance(PyType):
    def __init__(self, klass):
        self.klass = klass

@typed
def tyinstance(ty, tyclass) -> bool:
    try:
        return isinstance(ty, tyclass) or ty == tyclass or ty == tyclass.builtin
    except AttributeError:
        return False

@typed
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

@typed 
def has_type(val, ty) -> bool:
    if tyinstance(ty, Dyn):
        return True
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
        return isinstance(val, list) and \
            all(map(lambda x: has_type(x, ty.type), val))
    elif tyinstance(ty, Dict):
        return isinstance(val, dict) and \
            all(map(lambda x: has_type(x, ty.keys), val.keys())) and \
            all(map(lambda x: has_type(x, ty.values), val.values()))
    elif tyinstance(ty, Tuple):
        return isinstance(val, tuple) and len(ty.elements) == len(val) and \
            all(map(lambda p: has_type(p[0], p[1]), zip(val, ty.elements)))
    elif tyinstance(ty, Class):
        if inspect.isclass(val):
            for k in ty.members:
                if not has_type(getattr(val, k, False), ty.members[k]):
                    return False
            return True
        else: return False
    elif tyinstance(ty, Object):
        for k in ty.members:
            if not has_type(getattr(val, k, False), ty.members[k]):
                return False
        return True
    elif tyinstance(ty, Instance):
        return isinstance(val, ty.klass)
    elif inspect.isclass(ty):
        return isinstance(val, ty)
    else: raise UnknownTypeError('Unknown type ', ty)
