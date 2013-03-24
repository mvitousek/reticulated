from typing import * 

class Bot(Exception):
    pass

def tymeet(types):
    types = list(map(normalize, types))
    meet = types[0]
    for ty in types[1:]:
        if tyinstance(meet, Dyn):
            meet = ty
        elif tyinstance(ty, Dyn):
            continue
        elif not tyinstance(ty, normalize(meet).__class__):
            raise Bot()
        elif tyinstance(ty, List):
            join = List(tymeet([ty.type, meet.type]))
        elif tyinstance(ty, Tuple):
            if len(ty.elements) == len(join.elements):
                meet = Tuple(*[tymeet(list(p)) for p in zip(ty.elements, meet.elements)])
            else: raise Bot()
        elif tyinstance(ty, Dict):
            meet = Dict(tymeet([ty.keys, meet.keys]), tymeet([ty.values, meet.values]))
        elif tyinstance(ty, Function):
            if len(ty.froms) == len(meet.froms):
                meet = Function([tymeet(list(p)) for p in zip(ty.froms, meet.froms)], 
                                tymeet([ty.to, meet.to]))
            else: raise Bot()
        elif tyinstance(ty, Object):
            members = {}
            for x in ty.members:
                if x in meet.members:
                    members[x] = tymeet([ty.members[x], meet.members[x]])
                else: members[x] = ty.members[x]
            for x in meet.members:
                if not x in members:
                    members[x] = meet.members[x]
            meet = Object(members)
    return meet

def prim_subtype(t1, t2):
    prims = [Bool, Int, Float, Complex]
    t1tys = [tyinstance(t1, ty) for ty in prims]
    t2tys = [tyinstance(t2, ty) for ty in prims]
    if not(any(t1tys)) or not(any(t2tys)):
        raise UnexpectedTypeError()
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

    if any(isinstance(op, o) for o in [ast.FloorDiv, ast.Mod]):
        if any(tyinstance(nd, ty) for nd in [l, r] for ty in [Complex, String, List, Tuple, Dict]):
            raise Bot
    if shifting(op) or logical(op):
        if any(tyinstance(nd, ty) for nd in [l, r] for ty in [Float, Complex, String, List, Tuple, Dict]):
            raise Bot
    if arith(op):
        if any(tyinstance(nd, ty) for nd in [l, r] for ty in [Dict]):
            raise Bot
        if not isinstance(op, ast.Add) and not isinstance(op, ast.Mult) and \
                any(tyinstance(nd, ty) for nd in [l, r] for ty in [String, List, Tuple]):
            raise Bot
    if any(tyinstance(nd, ty) for nd in [l, r] for ty in [Object, Dyn]):
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
        
        
        
