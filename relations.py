from typing import * 

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
