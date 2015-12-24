from .rtypes import *
from . import flags, logging
from .exc import UnknownTypeError, UnexpectedTypeError


def info_join(ty1, ty2):
    def memjoin(m1, m2):
        mems = {}
        for k in m1:
            if k in m2:
                mems[k] = ijoin(m1[k], m2[k])
            else: mems[k] = m1[k]
        for k in m2:
            if k not in m1:
                mems[k] = m2[k]
        return mems

    def ijoin(ty1, ty2):
        assert isinstance(ty1, PyType)
        assert isinstance(ty2, PyType)
        if not ty1.top_free() and ty2.top_free():
            return InfoTop
        elif tyinstance(ty1, Dyn):
            return ty2
        elif tyinstance(ty2, Dyn):
            return ty1
        elif ty1 == ty2:
            return ty1
        elif tyinstance(ty1, Function) and tyinstance(ty2, Function):
            return Function(info_paramjoin(ty1.froms, ty2.froms), ijoin(ty1.to, ty2.to))
        elif tyinstance(ty1, Object) and tyinstance(ty2, Object):
            name = ty1.name if ty1.name == ty2.name else ''
            ty1 = ty1.substitute(ty1.name, TypeVariable(name), False)
            ty2 = ty2.substitute(ty2.name, TypeVariable(name), False)
            mems = memjoin(ty1.members, ty2.members)  
            return Object(name, mems)
        elif tyinstance(ty1, Class) and tyinstance(ty2, Class):
            name = ty1.name if ty1.name == ty2.name else ''
            ty1 = ty1.substitute(ty1.name, TypeVariable(name), False)
            ty2 = ty2.substitute(ty2.name, TypeVariable(name), False)
            mems = memjoin(ty1.members, ty2.members)
            inst = memjoin(ty1.instance_members, ty2.instance_members)
            return Class(name, mems, inst)
        elif tyinstance(ty1, List) and tyinstance(ty2, List):
            return List(ijoin(ty1.type, ty2.type))
        elif tyinstance(ty1, Set) and tyinstance(ty2, Set):
            return Set(ijoin(ty1.type, ty2.type))
        elif tyinstance(ty1, Dict) and tyinstance(ty2, Dict):
            return Dict(ijoin(ty1.keys, ty2.keys), ijoin(ty1.values, ty2.values))
        elif tyinstance(ty1, Tuple) and tyinstance(ty2, Tuple):
            if len(ty1.elements) == len(ty2.elements):
                Tuple(*[ijoin(e1, e2) for (e1, e2) in zip(ty1.elements, ty2.elements)])
            else: return InfoTop
        elif tyinstance(ty1, Structural) and tyinstance(ty2, Structural) and \
             (tyinstance(ty1, Object) or tyinstance(ty2, Object)):
            return ijoin(ty1.structure(), ty2.structure())
        else: return InfoTop
    join = ijoin(ty1, ty2)
    if join.top_free():
        return join
    else: return InfoTop

def n_info_join(*types):
    if type(types[0]) == list and len(types) == 1:
        types = types[0]
    if len(types) == 0:
        return Dyn
    join = types[0]
    for ty in types[1:]:
        join = info_join(join, ty)
        if not join.top_free() or not ty.top_free():
            return InfoTop
    return join

def info_paramjoin(p1, p2):
    if pinstance(p1, DynParameters):
        return p2
    elif pinstance(p2, DynParameters):
        return p1
    elif pinstance(p1, NamedParameters):
        if len(p1.parameters) != len(p2.parameters):
            return InfoTop
        elif pinstance(p2, NamedParameters):
            if all(k1 == k2 for (k1, _), (k2, _) in zip(p1.parameters, p2.parameters)):
                return NamedParameters([(k1, info_join(t1, t2)) for (k1, t1), (_, t2) in\
                                            zip(p1.parameters, p2.parameters)])
            else: return InfoTop
        elif pinstance(p2, AnonymousParameters):
            return AnonymousParameters([info_join(t1, t2) for t1, (_, t2) in\
                                            zip(p2.parameters, p1.parameters)])
        else: raise UnknownTypeError()
    elif pinstance(p1, AnonymousParameters):
        if len(p1.parameters) != len(p2.parameters):
            return InfoTop
        elif pinstance(p2, NamedParameters):
            return AnonymousParameters([info_join(t1, t2) for t1, (_, t2) in\
                                            zip(p1.parameters, p2.parameters)])
        elif pinstance(p2, AnonymousParameters):
            return AnonymousParameters([info_join(t1, t2) for t1, t2 in\
                                            zip(p1.parameters, p2.parameters)])
        else: raise UnknownTypeError()
    else: raise UnknownTypeError()

def prim_subtype(t1, t2):
    prims = [Bool, Int, Float, Complex]
    t1tys = [tyinstance(t1, ty) for ty in prims]
    t2tys = [tyinstance(t2, ty) for ty in prims]
    if not(any(t1tys)) or not(any(t2tys)):
        return False
    return t1tys.index(True) <= t2tys.index(True)

def primjoin(tys, min=Int, max=Complex):
    try:
        ty = tys[0]
        for ity in tys[1:]:
            if prim_subtype(ty, ity):
                ty = ity
        if not prim_subtype(ty, max):
            return Dyn
        if prim_subtype(ty, min):
            return min
        else: return ty
    except UnexpectedTypeError:
        return Dyn
    except IndexError:
        return Dyn

def binop_type(l, op, r):
    if tyinstance(l, InferBottom) or tyinstance(r, InferBottom):
        return InferBottom
    if not flags.MORE_BINOP_CHECKING and (tyinstance(l, Dyn) or tyinstance(r, Dyn)):
        return Dyn

    def prim(ty):
        return any(tyinstance(ty, t) for t in [Bool, Int, Float, Complex])
    def intlike(ty):
        return any(tyinstance(ty, t) for t in [Bool, Int])
    def arith(op):
        return any(isinstance(op, o) for o in [ast.Add, ast.Mult, ast.Div, ast.FloorDiv, ast.Sub, ast.Pow])
    def shifting(op):
        return any(isinstance(op, o) for o in [ast.LShift, ast.RShift])
    def logical(op):
        return any(isinstance(op, o) for o in [ast.BitOr, ast.BitAnd, ast.BitXor])
    def listlike(ty):
        return any(tyinstance(ty, t) for t in [List, String])

    if isinstance(op, ast.FloorDiv):
        if any(tyinstance(nd, ty) for nd in [l, r] for ty in [String, Complex, List, Tuple, Dict]):
            return InfoTop
    if isinstance(op, ast.Mod):
        if any(tyinstance(l, ty) for ty in [Complex, List, Tuple, Dict]):
            return InfoTop
    if shifting(op) or logical(op):
        if any(tyinstance(nd, ty) for nd in [l, r] for ty in [Float, Complex, String, List, Tuple, Dict]):
            return InfoTop
    if arith(op):
        if any(tyinstance(nd, ty) for nd in [l, r] for ty in [Dict]):
            return InfoTop
        if not isinstance(op, ast.Add) and not isinstance(op, ast.Mult) and \
                any(tyinstance(nd, ty) for nd in [l, r] for ty in [String, List, Tuple]):
            return InfoTop
    if any(tyinstance(nd, ty) for nd in [l, r] for ty in [Object, Dyn]):
        return Dyn
    
    if tyinstance(l, Bool):
        if arith(op) or shifting(op) or isinstance(op, ast.Mod):
            if isinstance(op, ast.Div) and prim_subtype(r, Float):
                return Float
            if tyinstance(r, Bool):
                return Int
            elif prim(r):
                return r
            elif listlike(r) and isinstance(op, ast.Mult):
                return r
            elif tyinstance(r, Tuple) and isinstance(op, ast.Mult):
                return Dyn
            else: return InfoTop
        elif logical(op):
            return r
        else:
            return InfoTop
    elif tyinstance(l, Int):
        if isinstance(op, ast.Div) and prim_subtype(r, Float):
            return Float
        elif listlike(r) and isinstance(op, ast.Mult):
            return r
        elif isinstance(r, Tuple) and isinstance(op, ast.Mult):
            return Dyn
        elif prim_subtype(r, l):
            return l
        elif prim_subtype(l, r):
            return r
        else:
            return InfoTop
    elif prim(l):
        if prim_subtype(r, l):
            return l
        elif prim_subtype(l, r):
            return r
        else:
            return InfoTop
    elif listlike(l):
        if intlike(r) and isinstance(op, ast.Mult):
            return l
        elif tyinstance(l, String) and isinstance(op, ast.Mod):
            return l
        elif any(tyinstance(l, ty) and tyinstance(r, ty) for ty in [List, String]) and isinstance(op, ast.Add):
            return tyjoin([l, r])
        else:
            return InfoTop
    elif tyinstance(l, Tuple):
        if intlike(r) and isinstance(op, ast.Mult):
            return Dyn
        elif tyinstance(r, Tuple) and isinstance(op, ast.Add):
            return Tuple(*(l.elements + r.elements))
        else:
            return InfoTop
    else:
        return Dyn

def subcompat(ty1, ty2, env=None, ctx=None):
    if env == None:
        env = {}

    if not ty1.top_free() or not ty2.top_free():
        return False

    return subtype(env, ctx, merge(ty1, ty2), ty2)

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
    elif isinstance(ty, tuple):
        return Tuple(*[normalize(t) for t in ty])
    elif isinstance(ty, dict):
        nty = {}
        for k in ty:
            if type(k) != str:
                raise UnknownTypeError()
            nty[k] = normalize(ty[k])
        return Object('', nty)
    elif ty is Object:
        return normalize(Object('', {}))
    elif ty is Class:
        return normalize(Class('', {}, {}))
    elif tyinstance(ty, Object):
        nty = {}
        for k in ty.members:
            if type(k) != str:
                raise UnknownTypeError()
            nty[k] = normalize(ty.members[k])
        return Object(ty.name, nty)
    elif tyinstance(ty, Class):
        nty = {}
        for k in ty.members:
            if type(k) != str:
                raise UnknownTypeError()
            nty[k] = normalize(ty.members[k])
        ity = {}
        for k in ty.instance_members:
            if type(k) != str:
                raise UnknownTypeError()
            ity[k] = normalize(ty.instance_members[k])
        return Class(ty.name, nty, ity)
    elif tyinstance(ty, Tuple):
        return Tuple(*[normalize(t) for t in ty.elements])
    elif tyinstance(ty, Function):
        return Function(normalize_params(ty.froms), normalize(ty.to))
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

def normalize_params(params):
    if pinstance(params, AnonymousParameters):
        return AnonymousParameters([normalize(p) for p in params.parameters])
    elif pinstance(params, NamedParameters):
        return NamedParameters([(k, normalize(p)) for k,p in params.parameters])
    elif pinstance(params, DynParameters):
        return params
    else: raise UnknownTypeError()

def widen(*types):
    join = tyjoin(types)

def tyjoin(*types):
    if isinstance(types[0], list) and len(types) == 1:
        types = types[0]
    if len(types) == 0:
        return Dyn
    if all(tyinstance(x, InferBottom) for x in types):
        return InferBottom
    types = [ty for ty in types if not tyinstance(ty, InferBottom)]
    if len(types) == 0:
        return Dyn
    join = types[0]
    if tyinstance(join, Dyn):
        return Dyn
    for ty in types[1:]:
        if not flags.FLAT_PRIMITIVES:
            pjoin = primjoin([join, ty])
            if not tyinstance(pjoin, Dyn):
                join = pjoin

        if not tyinstance(ty, join.__class__) or \
                tyinstance(ty, Dyn):
            return Dyn
        elif tyinstance(ty, TypeVariable):
            if ty.name == join.name:
                continue
            else: return Dyn
        elif tyinstance(ty, List):
            join = List(tyjoin([ty.type, join.type]))
        elif tyinstance(ty, Tuple):
            if len(ty.elements) == len(join.elements):
                join = Tuple(*[tyjoin(list(p)) for p in zip(ty.elements, join.elements)])
            else: return Dyn
        elif tyinstance(ty, Dict):
            join = Dict(tyjoin([ty.keys, join.keys]), tyjoin([ty.values, join.values]))
        elif tyinstance(ty, Function):
            join = Function(paramjoin(ty.froms, join.froms), 
                            tyjoin([ty.to, join.to]))
        elif tyinstance(ty, Object) or tyinstance(ty, Class):
            name = ty.name if ty.name == join.name else ''
            members = {}
            for x in ty.members:
                if x in join.members:
                    members[x] = tyjoin([ty.members[x], join.members[x]])
            if tyinstance(ty, Class) and tyinstance(join, Class):
                imems = {}
                for x in ty.instance_members:
                    if x in join.instance_members:
                        imems[x] = tyjoin([ty.instance_members[x], join.instance_members[x]])
                join = Class(name, members, imems)
            else: join = ty.__class__(name,members)
        if join == Dyn: return Dyn
    return join

def paramjoin(p1, p2):
    if pinstance(p1, DynParameters):
        return p1
    elif pinstance(p2, DynParameters):
        return p2
    elif pinstance(p1, NamedParameters):
        if len(p1.parameters) != len(p2.parameters):
            return DynParameters
        elif pinstance(p2, NamedParameters):
            if all(k1 == k2 for (k1, _), (k2, _) in zip(p1.parameters, p2.parameters)):
                return NamedParameters([(k1, tyjoin(t1, t2)) for (k1, t1), (_, t2) in\
                                            zip(p1.parameters, p2.parameters)])
            else: 
                return AnonymousParameters([tyjoin(t1, t2) for (_, t1), (_, t2) in\
                                                zip(p1.parameters, p2.parameters)])
        elif pinstance(p2, AnonymousParameters):
            return AnonymousParameters([tyjoin(t1, t2) for t1, (_, t2) in\
                                            zip(p2.parameters, p1.parameters)])
        else: raise UnknownTypeError()
    elif pinstance(p1, AnonymousParameters):
        if len(p1.parameters) != len(p2.parameters):
            return DynParameters
        elif pinstance(p2, NamedParameters):
            return AnonymousParameters([tyjoin(t1, t2) for t1, (_, t2) in\
                                             zip(p1.parameters, p2.parameters)])
        elif pinstance(p2, AnonymousParameters):
            return AnonymousParameters([tyjoin(t1, t2) for t1, t2 in\
                                             zip(p1.parameters, p2.parameters)])
        else: raise UnknownTypeError()
    else: raise UnknownTypeError()

def shallow(ty):
    return ty.__class__
    
def param_subtype(env, ctx, p1, p2):
    
    if p1 == p2:
        return True
    elif pinstance(p1, NamedParameters):
        if pinstance(p2, NamedParameters):
            return len(p1.parameters) == len(p2.parameters) and\
                all(((k1 == k2 or not flags.PARAMETER_NAME_CHECKING) and subtype(env, ctx, f2, f1)) for\
                        (k1,f1), (k2,f2) in zip(p1.parameters, p2.parameters)) # Covariance handled here
        elif pinstance(p2, AnonymousParameters):
            return len(p1.parameters) == len(p2.parameters) and\
                all(subtype(env, ctx, f2, f1) for (_, f1), f2 in\
                        zip(p1.parameters, p2.parameters))
        else: return False
    elif pinstance(p1, AnonymousParameters):
        if pinstance(p2, AnonymousParameters):
            return len(p1.parameters) == len(p2.parameters) and\
                all(subtype(env, ctx, f2, f1) for f1, f2 in zip(p1.parameters,
                                                                p2.parameters))
        elif pinstance(p1, NamedParameters):
            return len(p1.parameters) == len(p2.parameters) and len(p1.parameters) == 0
        else: return False
    else: return False
        
def subtype(env, ctx, ty1, ty2):
    if not flags.FLAT_PRIMITIVES and prim_subtype(ty1, ty2):
        return True
    elif ty1 == ty2:
        return True
    elif tyinstance(ty2, InfoTop):
        return True
    elif tyinstance(ty1, InferBottom) or tyinstance(ty2, InferBottom):
        return True
    elif tyinstance(ty2, Bytes):
        return tyinstance(ty1, Bytes)
    elif tyinstance(ty2, List):
        if tyinstance(ty1, List):
            return ty1.type == ty2.type
        else: return False
    elif tyinstance(ty2, Tuple):
        if tyinstance(ty1, Tuple):
            return len(ty1.elements) == len(ty2.elements) and \
                all(e1 == e2 for e1, e2 in zip(ty1.elements, ty2.elements))
        else: return False
    elif tyinstance(ty2, Function):
        if tyinstance(ty1, Function):
            return param_subtype(env, ctx, ty1.froms, ty2.froms) and subtype(env, ctx, ty1.to, ty2.to) # Covariance DOES NOT happen here, it's in param_subtype
        elif tyinstance(ty1, Class):
            if '__new__' in ty1.members:
                fty = ty1.member_type('__new__')
                if tyinstance(fty, Dyn):
                    fty = fty.bind()
            elif '__init__' in ty1.members:
                fty = ty1.member_type('__init__')
                if tyinstance(fty, Dyn):
                    fty = fty.bind()
            else: fty = Function(DynParameters, ty1.instance())
            return subtype(env, ctx, fty, ty2)
        elif tyinstance(ty1, Object):
            if '__call__' in ty1.members:
                return subtype(env, ctx, ty1.member_type('__call__'), ty2)
            else: return False
        else: return False
    elif tyinstance(ty2, Object):
        if tyinstance(ty1, Object):
            for m in ty2.members:
                if m not in ty1.members or ty1.members[m].substitute(ty1.name, TypeVariable(ty2.name), False)\
                        != ty2.members[m]:
                    logging.debug('Object not a subtype due to member %s: %s =/= %s' %\
                                     (m, ty1.members.get(m, None),
                                      ty2.members[m]), flags.SUBTY)
                    return False
            return True
        elif tyinstance(ty1, Self):
            if ctx:
                return subtype(env, ctx, ctx.instance(), ty2)
            else:
                return True
        else: return False
    elif tyinstance(ty2, Class):
        if tyinstance(ty1, Class):
            return all((m in ty1.members and ty1.member_type(m) == ty2.member_type(m)) for m in ty2.members) and \
                all((m in ty1.instance_members and ty1.instance_member_type(m) == ty2.instance_member_type(m)) for m in ty2.instance_members)
        else: return False
    elif tyinstance(ty2, Self):
        if ctx:
            return subtype(env, ctx, ty1, ctx.instance())
        else:
            return tyinstance(ty1, Object)
    elif tyinstance(ty2, TypeVariable):
        return subtype(env, ctx, ty1, env[ty2])
    elif tyinstance(ty1, TypeVariable):
        return subtype(env, ctx, env[ty1], ty2)
    elif tyinstance(ty1, Base):
        return tyinstance(ty2, shallow(ty1))
    else: return False

def merge(ty1, ty2):
    if tyinstance(ty1, Dyn):
        return ty2
    elif tyinstance(ty2, Dyn):
        return Dyn
    if tyinstance(ty1, List):
        if tyinstance(ty2, List):
            return List(merge(ty1.type, ty2.type))
        elif tyinstance(ty2, Tuple):
            return Tuple(*[merge(ty1.type, ty2m) for ty2m in ty2.elements])
        else: return ty1
    if tyinstance(ty1, Dict):
        if tyinstance(ty2, Dict):
            return Dict(merge(ty1.keys, ty2.keys), merge(ty1.values, ty2.values))
        else: return ty1
    if tyinstance(ty1, Tuple):
        if tyinstance(ty2, Tuple) and len(ty1.elements) == len(ty2.elements):
            return Tuple(*[merge(e1, e2) for e1, e2 in zip(ty1.elements, ty2.elements)])
        else: return ty1
    elif tyinstance(ty1, Object):
        if tyinstance(ty2, Object):
            nty = {}
            for n in ty1.members:
                if n in ty2.members:
                    nty[n] = merge(ty1.members[n],ty2.members[n])
                elif flags.MERGE_KEEPS_SOURCES: nty[n] = ty1.members[n]
            if not flags.CLOSED_CLASSES:
                for n in ty2.members:
                    if n not in nty:
                        nty[n] = ty2.members[n]
            return Object(ty1.name, nty)
        elif tyinstance(ty2, Function):
            if '__call__' in ty1.members:
                cty = merge(ty1.members['__call__'],ty2)
            else: cty = ty2
            return Object(ty1.name, {'__call__': ty2})
        else: return ty1
    elif tyinstance(ty1, Class):
        if tyinstance(ty2, Class):
            nty = {}
            for n in ty1.members:
                if n in ty2.members:
                    nty[n] = merge(ty1.members[n],ty2.members[n])
                elif flags.MERGE_KEEPS_SOURCES: nty[n] = ty1.members[n]
            if not flags.CLOSED_CLASSES:
                for n in ty2.members:
                    if n not in nty:
                        nty[n] = ty2.members[n]
            ity = {}
            for n in ty1.instance_members:
                if n in ty2.instance_members:
                    nty[n] = merge(ty1.instance_members[n],ty2.instance_members[n])
                elif flags.MERGE_KEEPS_SOURCES: nty[n] = ty1.instance_members[n]
            if not flags.CLOSED_CLASSES:
                for n in ty2.instance_members:
                    if n not in nty:
                        nty[n] = ty2.instance_members[n]
            return Class(ty1.name, nty, ity)
        else: return ty1
    elif tyinstance(ty1, Function):
        if tyinstance(ty2, Function):
            return Function(merge_params(ty1.froms, ty2.froms), merge(ty1.to, ty2.to))
        else: return ty1
    else: return ty1

def merge_params(p1, p2):
    if pinstance(p1, DynParameters):
        return p2
    elif pinstance(p2, DynParameters):
        return DynParameters
    else:
        args = p2.lenmatch(p1.parameters)
        if args == None:
            return p1
        elif pinstance(p1, AnonymousParameters):
            return AnonymousParameters([merge(t1, t2) for t1, t2 in args])
        elif pinstance(p1, NamedParameters):
            return NamedParameters([(k, merge(t1, t2)) for (k,t1), t2 in zip(p1.parameters, map(lambda x: x[1], args))])
        else: raise UnknownTypeError()
