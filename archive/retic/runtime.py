import inspect, types
from . import flags
from . import relations
from .rtypes import *
from .exc import UnknownTypeError, UnexpectedTypeError

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
    

def retic_bindmethod(cls, receiver, attr):
    val = getattr(receiver, attr)
    if inspect.ismethod(val):
        return lambda *args: getattr(cls, attr)(receiver, *args)
    else: return val

if flags.INITIAL_ENVIRONMENT:
    def dyn(v):
        return v

### Python 2.7 annotation
def retic_typed(ty=None, error_function='retic_error'):
    def tyfn(fn):
        if tyinstance(ty, Function):
            spec = inspect.getargspec(fn)
            posargs = spec.args
            annotations = ty.froms.lenmatch(posargs)
            if annotations == None:
                error_function('Mismatch in number of positional arguments')
            annotations = dict(annotations)
            annotations['return'] = ty.to
            fn.__annotations__ = annotations
        elif tyinstance(ty, Class):
            pass
        else:
            error_function('Functions must be annotated with function types')
        return fn
    return tyfn

typed = retic_typed

def infer(k):
    return k

def noinfer(k):
    return k

def parameters(*k):
    return lambda x: x

def returns(k):
    return lambda x: x

def fields(k):
    return lambda x: x

def members(k):
    return lambda x: x


### Metaclass constructor for monotonic objects
def _monotonic(metaclass):
    class Monotonic(metaclass):
        monotonic_capable_class = True
    return Monotonic
Monotonic = _monotonic(type)

def has_type(val, ty):
    return has_type_depth(val, ty, 0)

def rse(x=None):
    raise Exception(x)

def check_type_int(val):
    return val if isinstance(val, int) else (check_type_bool(val) if not flags.FLAT_PRIMITIVES else rse(val))

def check_type_void(val):
    return val if val is None else rse()

def check_type_bytes(val):
    return val if isinstance(val, bytes) else rse()

def check_type_bool(val):
    return val if isinstance(val, bool) else rse(val)

def check_type_float(val):
    return val if isinstance(val, float) else (check_type_int(val) if not flags.FLAT_PRIMITIVES else rse(val))

def check_type_complex(val):
    return val if isinstance(val, complex) else (check_type_float(val) if not flags.FLAT_PRIMITIVES else rse(val))

def check_type_string(val):
    return val if isinstance(val, str) else rse()

def check_type_function(val):
    return val if callable(val) or isinstance(val, classmethod)  else rse()

def check_type_list(val):
    return val if (isinstance(val, list)) else rse()

def check_type_tuple(val, n):
    return val if (isinstance(val, tuple) or isinstance(val, list)) and len(val) == n else rse()

def check_type_dict(val):
    return val if isinstance(val, dict) else rse()
    
def check_type_object(val, mems):
#    return val if set(mems).issubset(dir(val)) else rse() 6s

    # d = dir(val)
    # return val if all(x in d for x in mems) else rse() 5s

    for k in mems:
        if not hasattr(val, k):# or not check_type_depth(getattr(val, k), ty.members[k], depth+1):
            rse((type(val), k))
    return val

def check_type_class(val, mems):

    for k in mems:
        if not hasattr(val, k):# or not check_type_depth(getattr(val, k), ty.members[k], depth+1):
            rse()
    return val if type in inspect.getmro(val.__class__) else rse()



def has_type_depth(val, ty, depth):
    if depth > flags.CHECK_DEPTH:
        return True
    elif ty is TypeVariable:
        return True
    elif ty is Self:
        return True
    elif ty is Dyn:
        return True
    elif ty is InferBottom:
        return False
    elif ty is Void:
        return val == None
    elif ty is Int:
        return isinstance(val, int) or (not flags.FLAT_PRIMITIVES and has_type(val, Bool))
    elif ty is Bytes:
        return isinstance(val, bytes)
    elif ty is Bool:
        return isinstance(val, bool)
    elif ty is Float:
        return isinstance(val, float) or (not flags.FLAT_PRIMITIVES and has_type(val, Int))
    elif ty is Complex:
        return isinstance(val, complex) or (not flags.FLAT_PRIMITIVES and has_type(val, Float))
    elif ty is String:
        return isinstance(val, str)
    elif isinstance(ty, Function):
        if callable(val): 
            return True
        else: return False

        if val.__class__ is types.MethodType: # Only true for bound methods
            spec = getfullargspec(val)
            new_spec = inspect.FullArgSpec(spec.args[1:], spec.varargs, spec.varkw, 
                                           spec.defaults, spec.kwonlyargs, 
                                           spec.kwonlydefaults, spec.annotations)
            return func_has_type(new_spec, ty)
        elif val.__class__ is types.FunctionType: # Normal function
            return func_has_type(getfullargspec(val), ty)
        elif val.__class__ is type: 
            if val.__init__.__class__ is types.FunctionType:
                spec = getfullargspec(val.__init__)
                new_spec = inspect.FullArgSpec(spec.args[1:], spec.varargs, spec.varkw, 
                                               spec.defaults, spec.kwonlyargs, 
                                               spec.kwonlydefaults, spec.annotations)
                return func_has_type(new_spec, ty)
            else: return True
        elif val.__class__ is types.BuiltinFunctionType:
            return True
        elif hasattr(val, '__call__'):
            if val.__call__.__class__ is types.MethodType:
                spec = getfullargspec(val.__call__)
                new_spec = inspect.FullArgSpec(spec.args[1:], spec.varargs, spec.varkw, 
                                               spec.defaults, spec.kwonlyargs, 
                                               spec.kwonlydefaults, spec.annotations)
                return func_has_type(new_spec, ty)
            else: return True
        elif callable(val):
            return True # No clue
        else: return False
    elif isinstance(ty, List):
        return (isinstance(val, list))
# and \
#            all(map(lambda x: has_type_depth(x, ty.type, depth+1), val))
    elif isinstance(ty, Set):
        return isinstance(val, set) and \
            all(map(lambda x: has_type_depth(x, ty.type, depth+1), val))
    elif isinstance(ty, Dict):
        return isinstance(val, dict)# and \
#            all(map(lambda x: has_type_depth(x, ty.keys, depth+1), val.keys())) and \
#            all(map(lambda x: has_type_depth(x, ty.values, depth+1), val.values()))
    elif isinstance(ty, Tuple):
        return (isinstance(val, tuple) or isinstance(val, list))# \
#            and len(ty.elements) == len(val) and \
#            all(map(lambda p: has_type_depth(p[0], p[1], depth+1), zip(val, ty.elements)))
    # elif isinstance(ty, Iterable):
    #     if (isinstance(val, tuple) or isinstance(val, list) or isinstance(val, set)) or iter(val) is not val:
    #         return all(map(lambda x: has_type_depth(x, ty.type, depth+1), val))
    #     elif isinstance(val, collections.Iterable):
    #         if hasattr(val, '__iter__'):
    #             return has_type_depth(val.__iter__, Function([Dyn], Iterable(ty.type)), depth+1)
    #         else: return True
    #     else: return False
    elif isinstance(ty, Object):
        for k in ty.members:
            if not hasattr(val, k):# or not has_type_depth(getattr(val, k), ty.members[k], depth+1):
                return False
        return True
    elif isinstance(ty, Class):
        for k in ty.members:
            if not hasattr(val, k):# or not has_type_depth(getattr(val, k), ty.members[k], depth+1):
                return False
        return isinstance(val, type)
    else: raise UnknownTypeError('Unknown type ', ty)

def has_shape(obj, dct):
    for k in dct:
        try: getattr(obj, k)
        except AttributeError:
            return False
    return True

def runtime_type(ty):
    try: 
        ty.static()
        return ty
    except AttributeError:
        return Dyn

def func_has_type(argspec, ty):
    if argspec.varargs != None or\
            argspec.varkw != None:
        return True
    if argspec.defaults == None:
        argset = ty.froms.lenmatch(argspec.args)
        if argset == None:
            return False
    else:
        for i in range(len(argspec.args),
                       len(argspec.args)-len(argspec.defaults)-1,-1):
            argset = ty.froms.lenmatch(argspec.args[:i])
            if argset != None:
                break
        if argset == None:
            return False
    if not hasattr(argspec, 'annotations'):
        return True
    for p, t in argset:
        if p in argspec.annotations and\
                not relations.subcompat(t, runtime_type(argspec.annotations[p])):
            return False
    if 'return' in argspec.annotations:
        return relations.subcompat(runtime_type(argspec.annotations['return']), ty.to)
    else:
        return True
