from rtypes import *

class Bot(Exception):
    pass

def tymeet(*types):
    if isinstance(types[0], list) and len(types) == 1:
        types = types[0]
    types = list(map(normalize, types))
    meet = types[0]
    for ty in types[1:]:
        if tyinstance(meet, Dyn):
            meet = ty
        elif tyinstance(ty, Dyn):
            continue
        elif not tyinstance(ty, normalize(meet).__class__):
            return Bottom
        elif tyinstance(ty, List):
            join = List(tymeet([ty.type, meet.type]))
        elif tyinstance(ty, Tuple):
            if len(ty.elements) == len(join.elements):
                meet = Tuple(*[tymeet(list(p)) for p in zip(ty.elements, meet.elements)])
            else: return Bottom
        elif tyinstance(ty, Dict):
            meet = Dict(tymeet([ty.keys, meet.keys]), tymeet([ty.values, meet.values]))
        elif tyinstance(ty, Function):
            if len(ty.froms) == len(meet.froms):
                meet = Function([tymeet(list(p)) for p in zip(ty.froms, meet.froms)], 
                                tymeet([ty.to, meet.to]))
            else: return Bottom
        elif tyinstance(ty, Record):
            members = {}
            for x in ty.members:
                if x in meet.members:
                    members[x] = tymeet([ty.members[x], meet.members[x]])
                else: members[x] = ty.members[x]
            for x in meet.members:
                if not x in members:
                    members[x] = meet.members[x]
            meet = Record(members)
    return meet

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
    def prim(ty):
        return any(tyinstance(ty, t) for t in [Bool, Int, Float, Complex])
    def intlike(ty):
        return any(tyinstance(ty, t) for t in [Bool, Int])
    def arith(op):
        return any(isinstance(op, o) for o in [ast.Add, ast.Mult, ast.Div, ast.FloorDiv, ast.Sub, ast.Pow, ast.Mod])
    def shifting(op):
        return any(isinstance(op, o) for o in [ast.LShift, ast.RShift])
    def logical(op):
        return any(isinstance(op, o) for o in [ast.BitOr, ast.BitAnd, ast.BitXor])
    def listlike(ty):
        return any(tyinstance(ty, t) for t in [List, String])

    if isinstance(op, ast.FloorDiv):
        if any(tyinstance(nd, ty) for nd in [l, r] for ty in [String, Complex, List, Tuple, Dict]):
            raise Bot
    if isinstance(op, ast.Mod):
        if any(tyinstance(l, ty) for ty in [Complex, List, Tuple, Dict]):
            raise Bot
    if shifting(op) or logical(op):
        if any(tyinstance(nd, ty) for nd in [l, r] for ty in [Float, Complex, String, List, Tuple, Dict]):
            raise Bot
    if arith(op):
        if any(tyinstance(nd, ty) for nd in [l, r] for ty in [Dict]):
            raise Bot
        if not isinstance(op, ast.Add) and not isinstance(op, ast.Mult) and not isinstance(op, ast.Mod) and \
                any(tyinstance(nd, ty) for nd in [l, r] for ty in [String, List, Tuple]):
            raise Bot
    if any(tyinstance(nd, ty) for nd in [l, r] for ty in [Record, Dyn]):
        return Dyn
    
    if tyinstance(l, Bool):
        if arith(op) or shifting(op):
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
            else: raise Bot
        elif logical(op):
            return r
        else:
            raise Bot
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
            raise Bot
    elif prim(l):
        if prim_subtype(r, l):
            return l
        elif prim_subtype(l, r):
            return r
        else:
            raise Bot
    elif listlike(l):
        if intlike(r) and isinstance(op, ast.Mult):
            return l
        elif tyinstance(l, String) and isinstance(op, ast.Mod):
            return l
        elif any(tyinstance(l, ty) and tyinstance(r, ty) for ty in [List, String]) and isinstance(op, ast.Add):
            return tyjoin([l, r])
        else:
            raise Bot
    elif tyinstance(l, Tuple):
        if intlike(r) and isinstance(op, ast.Mult):
            return Dyn
        elif tyinstance(r, Tuple) and isinstance(op, ast.Add):
            return Tuple(l.elements + r.elements)
        else:
            raise Bot
    else:
        return Dyn
    
def compat(env, ctx, ty1, ty2):
    if Dyn == ty1 or Dyn == ty2 or ty1 == ty2:
        return True
    elif (tyinstance(ty1, Record) or tyinstance(ty1, Object) or \
              tyinstance(ty1, Class)):
        if tyinstance(ty2, ty1.__class__) and ty1.members.keys() == ty2.members.keys():
            return all(compat(env, ctx, ty1.members[k], ty2.members[k]) for k in ty1.members)
        elif tyinstance(ty2, Self):
            pass
    elif tyinstance(ty1, Function) and tyinstance(ty2, Function) and len(ty1.froms) == len(ty2.froms):
        return all(compat(env, ctx, t2k, t1k) for t1k, t2k in zip(ty1.froms, ty2.froms)) and \
            compat(env, ctx, ty1.to, ty2.to)


def subcompat(ty1, ty2, env=None, ctx=None):
    if env == None:
        env = {}
    if ctx == None:
        ctx = Bottom()
    return subtype(env, ctx, merge(ty1, ty2), ty2)

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

def shallow(ty):
    return ty.__class__
    
def subtype(env, ctx, ty1, ty2):
    print(ty1, '<:?', ty2)
    if ty1 == ty2:
        return True
    elif tyinstance(ty2, Top) or tyinstance(ty1, Bottom):
        return True
    elif tyinstance(ty2, Bottom):
        return True # Supporting type inference, freakin weird
    elif tyinstance(ty1, Function):
        if tyinstance(ty2, Function) and len(ty1.froms) == len(ty2.froms):
            return all(subtype(env, ctx, f2, f1) for f1, f2 in zip(ty1.froms, ty2.froms)) and \
                subtype(env, ctx, ty1.to, ty2.to)
        else: return False
    elif tyinstance(ty2, Record):
        if tyinstance(ty1, Record):
            return all((m in ty1.members and subtype(env, ctx, ty1.members[m], ty2.members[m])) \
                           for m in ty2.members)
        elif tyinstance(ty1, Object) or tyinstance(ty1, Class):
            return all((m in ty1.members and ty1.member_type(m) == ty2.members[m]) for m in ty2.members)
        else: return False
    elif tyinstance(ty2, Object):
        if tyinstance(ty1, Object):
            for m in ty2.members:
                if m not in ty1.members or ty1.members[m] != ty2.members[m]:
                    return False
            return True
        elif tyinstance(ty1, Self):
            return subtype(env, ctx, ctx.instance(), ty2)
        else: return False
    elif tyinstance(ty2, Class):
        if tyinstance(ty1, Class):
            return all((m in ty1.members and ty1.member_type(m) != ty2.member_type(m)) for m in ty2.members)
        else: return True
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
    elif tyinstance(ty1, Record):
        if tyinstance(ty2, Record):
            nty = {}
            for n in ty1.members:
                if n in ty2.members:
                    nty[n] = merge(ty1.members[n],ty2.members[n])
                else: nty[n] = ty1.members[n]
            return Record(nty)
        else: return ty1
    elif tyinstance(ty1, Object):
        if tyinstance(ty2, Record) or tyinstance(ty2, Object):
            nty = {}
            for n in ty1.members:
                if n in ty2.members:
                    nty[n] = merge(ty1.members[n],ty2.members[n])
                else: nty[n] = ty1.members[n]
            return Object(ty1.name, nty)
        else: return ty1
    else: return ty1
