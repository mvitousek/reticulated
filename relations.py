from typing import * 

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
