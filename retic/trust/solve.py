from .constraints import *
from .ctypes import *
from .. import retic_ast

class BailOut(Exception): pass

def normalize(constraints, ctbl):
    print('\n\n\nCONSTRAINTS: ', constraints, '\n\nCTBL:', ctbl)
    def is_v(u, v):
        if u is v:
            return True
        elif isinstance(u, CVarBind):
            return is_v(u.var, v)
        else: return False
    def type_lower_bound(v, c):
        return isinstance(c, STC) and is_v(c.u, v) and not isinstance(c.l, CVar) and not isinstance(c.l, CVarBind)

    oc = None
    while oc != constraints:
        oc = constraints
        constraints = decompose(constraints, ctbl)
    for c in constraints:
        if isinstance(c, EqC) and isinstance(c.l, CVar) and c.l is not c.r:
            new_constraints = [old_c.subst(c.l, c.r) for old_c in constraints]
#            print('Substituting', c.l.name, 'to', c.r)
            [ctbl[cls].subst(c.l, c.r) for cls in ctbl]
            return normalize(new_constraints + [DefC(c.l, c.r)], ctbl)
        elif isinstance(c, EqC) and isinstance(c.r, CVar):
            return normalize([EqC(c.r, c.l)] + constraints, ctbl)
    vars = set(sum([c.vars(ctbl) for c in constraints], []))
    for v in vars:
        cprime = [c for c in constraints if not type_lower_bound(v, c)]
        lbs = [c for c in constraints if type_lower_bound(v, c)]
        deps = depends(v, constraints, ctbl)
        if all([c.solvable(v, set(), ctbl) for c in cprime]):
            # Since upper bounds can be CVarBinds, we might need to do something to "unbind" lower bounds on such variables when we solve them
            ty = join([lb.l for lb in lbs])
#            print('Solving', v.name, 'at', ty)
 
            return normalize(constraints + [EqC(v, ty)], ctbl)
    solving = False
    for v in vars:
        lbs = [c for c in constraints if type_lower_bound(v, c)]
        cprime = [c for c in constraints if not type_lower_bound(v, c) and not isinstance(c, STC)]
        if len(lbs) > 0 and any((isinstance(c, CheckC) and c.l is v) for c in cprime):
            solving = True
            ty = join([lb.l for lb in lbs])
#            print('Solving', v.name, 'at', ty, '(dangerous)')
            try:
                return normalize(constraints + [EqC(v, ty)], ctbl)
            except BailOut:
#                print('#Bailing1')
                continue
    if solving:
#        print('#Up one level1')
        raise BailOut()

    for v in vars:
        lbs = [c for c in constraints if type_lower_bound(v, c)]
        cprime = [c for c in constraints if not type_lower_bound(v, c) and not isinstance(c, STC)]
        if len(lbs) > 0:
            solving = True
            ty = join([lb.l for lb in lbs])
#            print('Solving', v.name, 'at', ty, '(very dangerous)')
            try:
                return normalize(constraints + [EqC(v, ty)], ctbl)
            except BailOut:
#                print('#Bailing2')
                continue
    if solving:
#        print('#Up one level2')
        raise BailOut()

    if any(not isinstance(c, DefC) for c in constraints):
        print('#Unsolved constraints:', [c for c in constraints if not isinstance(c, DefC)])
    return constraints

# def trans(constraints):
#     ret = set(constraints[:])
#     vars = sum([c.vars(ctbl) for c in constraints], [])
#     for v in vars:
#         lbs = [c for c in constraints if isinstance(c, STC) and c.u is v]
#         ubs = [c for c in constraints if isinstance(c, STC) and c.l is v]
#         ret |= {STC(l.l, u.u) for l in lbs for u in ubs}
#     return list(ret)
        

def join(tys):
    if len(tys) == 0:
        return CDyn()
    join = tys[0]
    for ty in tys[1:]:
        if isinstance(join, CDyn):
            return join
        elif isinstance(join, CVar):
            raise BailOut()
        elif isinstance(join, CSingletonInt):
            if isinstance(ty, CSingletonInt):
                if join.n == ty.n:
                    continue
                else:
                    join = CInt()
            elif isinstance(ty, CInt):
                join = CInt()
            elif isinstance(ty, CBool):
                join = CInt()
            elif isinstance(ty, CFloat):
                join = CFloat()
            else: return CDyn()
        elif isinstance(join, CInt):
            if isinstance(ty, CSingletonInt):
                continue
            elif isinstance(ty, CInt):
                continue
            elif isinstance(ty, CBool):
                continue
            elif isinstance(ty, CFloat):
                join = CFloat()
            else: return CDyn()
        elif isinstance(join, CBool):
            if isinstance(ty, CSingletonInt):
                join = CInt()
            elif isinstance(ty, CInt):
                join = CInt()
            elif isinstance(ty, CBool):
                continue
            elif isinstance(ty, CFloat):
                join = CFloat()
            else: return CDyn()
        elif isinstance(join, CFloat):
            if isinstance(ty, CSingletonInt):
                continue
            elif isinstance(ty, CInt):
                continue
            elif isinstance(ty, CBool):
                continue
            elif isinstance(ty, CFloat):
                continue
            else: return CDyn()
        elif isinstance(join, CVoid):
            if isinstance(ty, CVoid):
                continue
            else: return CDyn()
        elif isinstance(join, CFunction):
            if isinstance(ty, CFunction):
                if isinstance(join.froms, PosCAT):
                    if isinstance(ty.froms, PosCAT) and len(ty.froms.types) == len(join.froms.types):
                        continue
                    else: join = CFunction(ArbCAT(), join.to)
                else: join = CFunction(ArbCAT(), join.to)
            else: return CDyn()
        elif isinstance(join, CTuple):
            if isinstance(ty, CTuple) and len(ty.elts) == len(join.elts):
                continue
            else: return CDyn()
        elif isinstance(join, CHTuple):
            if isinstance(ty, CHTuple):
                continue
            else: return CDyn()
        elif isinstance(join, CList):
            if isinstance(ty, CList):
                continue
            else: return CDyn()
        elif isinstance(join, CClass):
            if isinstance(ty, CClass) and join.name == ty.name:
                continue
            else: return CDyn()
        elif isinstance(join, CInstance):
            if isinstance(ty, CInstance) and join.instanceof == ty.instanceof:
                continue
            else: return CDyn()
        elif isinstance(join, CStructural):
            if isinstance(ty, CStructural):
                join = CStructural({mem: join.members[mem] for mem in join.members if mem in ty.members})
            else: return CDyn()
        elif isinstance(join, CSubscriptable):
            if isinstance(ty, CSubscriptable):
                continue
            else: return CDyn()
        elif isinstance(join, CStr):
            if isinstance(ty, CStr):
                continue
            else: return CDyn()
    return join

def decompose_bivariant(constraints, c, l, r, ctbl, sym):
    ret = []
    assert not (isinstance(r, CVar) or isinstance(r, CDyn) or isinstance(r, CFunction)), (l, r)
    if isinstance(r, CList):
        if isinstance(l, CList):
            ret.append(EqC(l.elts, r.elts))
        elif isinstance(l, CSubscriptable):
            ret += [STC(CInt(), l.keys), EqC(l.elts, r.elts)]
        else: raise BailOut(l)
    elif isinstance(r, CHTuple):
        if isinstance(l, CHTuple):
            ret.append(EqC(l.elts, r.elts))
        elif isinstance(l, CSubscriptable):
            ret += [STC(CInt(), l.keys), EqC(l.elts, r.elts)]
        else: raise BailOut()
    elif isinstance(r, CSet):
        if isinstance(l, CSet):
            ret.append(EqC(l.elts, r.elts))
        else: raise BailOut()
    elif isinstance(r, CDict):
        if isinstance(l, CDict):
            ret.append(EqC(l.keys, r.keys))
            ret.append(EqC(l.values, r.values))
        elif isinstance(l, CSubscriptable):
            ret += [EqC(l.keys, r.keys), EqC(l.elts, r.keys)]
        else: raise BailOut()
    elif isinstance(r, CTuple):
        if isinstance(l, CTuple) and len(l.elts) == len(r.elts):
            ret += [EqC(le, re) for le, re in zip(l.elts, r.elts)]
        elif isinstance(l, CSubscriptable):
            ret += [STC(CInt(), r.keys), EqC(l.elts, CDyn())] + [EqC(elt, CDyn()) for elt in r.elts]
        elif isinstance(l, CDyn):
            ret += [EqC(CDyn(), re) for re in r.elts]
        else: raise BailOut(l, r)
    elif isinstance(r, CInstance):
        if unsolvable_inherits(r, constraints):
            ret.append(c)
        elif isinstance(l, CInstance):
            if unsolvable_inherits(l, constraints):
                ret.append(c)
            elif r.instanceof in ctbl[l.instanceof].superclasses(ctbl):
                pass
            else:
                raise BailOut(l, sym, r)
        else: raise BailOut(r,l)
    elif isinstance(r, CClass):
        if isinstance(l, CClass) and r.name == l.name:
            pass
        else: raise BailOut(r, l)
    elif isinstance(r, CStructural):
        if isinstance(l, CStructural):
            ret += [EqC(l.members[mem], r.members[mem]) for mem in l.members if mem in r.members]
        elif isinstance(l, CInstance):
            if unsolvable_inherits(l, constraints):
                ret.append(c)
            cls = ctbl[l.instanceof]
            ret += [EqC(cls.instance_lookup(mem, ctbl), r.members[mem]) for mem in r.members if cls.instance_supports(mem, ctbl)]
        elif isinstance(l, CClass):
            if unsolvable_inherits(l, constraints):
                ret.append(c)
            cls = ctbl[l.name]
            ret += [EqC(cls.lookup(mem, ctbl), r.members[mem]) for mem in r.members if cls.supports(mem, ctbl)]
            # We may need to set members not in the intersect to dyn
        else: raise BailOut()
    elif isinstance(r, CSubscriptable): # This may be able to be refined to subtyping in some cases if it goes back in decompose
        if isinstance(l, CSubscriptable):
            ret += [EqC(r.keys, l.keys), EqC(l.elts, r.elts)]
        elif isinstance(l, CList):
            ret += [STC(CInt(), r.keys), EqC(l.elts, r.elts)]
        elif isinstance(l, CStr):
            ret += [STC(CInt(), r.keys), EqC(CStr(), r.elts)]
        elif isinstance(l, CHTuple):
            ret += [STC(CInt(), r.keys), EqC(l.elts, r.elts)]
        elif isinstance(l, CTuple): # With check constraints maybe we can do something here
            
            ret += [STC(CInt(), r.keys), EqC(r.elts, CDyn())] + [EqC(elt, CDyn()) for elt in l.elts]
        elif isinstance(l, CDict):
            ret += [EqC(r.keys, l.keys), EqC(l.values, r.elts)]
        else: raise BailOut(l, r)
    elif isinstance(r, CPrimitive):
        if isinstance(l, CPrimitive):
            pass
        else: raise BailOut(r,l)
    elif isinstance(r, CVarBind):
        if isinstance(l, CVarBind):
            ret += [EqC(l.var, r.var)]
        elif isinstance(l, CDyn):
            ret += [EqC(CDyn(), r.var)]
        else: raise BailOut(c)
    else: raise BailOut(l ,r, type(l), type(r))
    return ret

def unsolvable_inherits(ty, constraints):
    us = [c.cls for c in constraints if isinstance(c, InheritsC)]
    return (isinstance(ty, CClass) and ty.name in us) or (isinstance(ty, CInstance) and ty.instanceof in us) 

def decompose(constraints, ctbl):
    ret = []
    for c in constraints:
        if isinstance(c, EltSTC):
            if isinstance(c.lc, CTuple):
                ret += [STC(l, c.u) for l in c.lc.elts]
            elif isinstance(c.lc, CList):
                ret.append(STC(c.lc.elts, c.u))
            elif isinstance(c.lc, CHTuple):
                ret.append(STC(c.lc.elts, c.u))
            elif isinstance(c.lc, CSet):
                ret.append(STC(c.lc.elts, c.u))
            elif isinstance(c.lc, CDict):
                ret.append(STC(c.lc.keys, c.u))
            elif isinstance(c.lc, CStr):
                ret.append(STC(CStr(), c.u))
            elif isinstance(c.lc, CDyn):
                ret.append(STC(CDyn(), c.u))
            elif isinstance(c.lc, CVar):
                ret.append(c)
            else:
                raise BailOut(c.lc)
        elif isinstance(c, InheritsC):
            if len(c.supers) == 0:
                continue
            cls = ctbl[c.cls]
            rsupers = []
            for sup in c.supers:
                if isinstance(sup, CClass):
                    cls.inherits.append(sup.name)
                elif isinstance(sup, CDyn):
                    cls.dynamized = True
                elif isinstance(sup, CVar):
                    rsupers.append(sup)
                else:
                    raise BailOut()
            if rsupers:
                ret.append(InheritsC(rsupers, c.cls))
        elif isinstance(c, BinopSTC):
            if not isinstance(c.lo, CVar) and not isinstance(c.ro, CVar) and \
               not isinstance(c.lo, CVarBind) and not isinstance(c.ro, CVarBind):
                sol, sp = binop_solve(c.lo, c.op, c.ro)
                ret.append(STC(sol, c.u))
                ret += sp
            else:
                ret.append(c)
        elif isinstance(c, UnopSTC):
            if not isinstance(c.lo, CVar) and not isinstance(c.lo, CVarBind):
                sol, sp = unop_solve(c.op, c.lo)
                ret.append(STC(sol, c.u))
                ret += sp
            else:
                ret.append(c)
        elif isinstance(c, STC):
            if isinstance(c.u, CVar):
                if c.u is not c.l:
                    ret.append(c)
            elif isinstance(c.u, CInstance) and isinstance(c.l, CInstance):
                if unsolvable_inherits(c.u, constraints) or unsolvable_inherits(c.l, constraints):
                    ret.append(c)
                if c.u.instanceof in ctbl[c.l.instanceof].superclasses(ctbl):
                    pass
                else:
                    raise BailOut(c)
            elif isinstance(c.l, CVar):
                ret.append(c)
            elif isinstance(c.l, CVarBind):
                if isinstance(c.u, CVarBind):
                    ret += [STC(c.l.var, c.u.var)]
                else:
                    ret.append(c)
            elif isinstance(c.u, CVarBind):
                if c.u is not c.l:
                    ret.append(c)
            elif isinstance(c.u, CDyn):
                if isinstance(c.l, CVar):
                    ret.append(c)
                elif isinstance(c.l, CFunction):
                    ret.append(STC(c.l.to, CDyn()))
                    if isinstance(c.l.froms, PosCAT):
                        ret += [STC(CDyn(), param) for param in c.l.froms.types]
                    elif isinstance(c.l.froms, SpecCAT):
                        params = argspec.params(c.l.froms.spec)
                        for l in params:
                            ret.append(STC(CDyn(), l.annotation))
                    elif isinstance(c.l.froms, ArbCAT):
                        pass
                    else: raise BailOut()
                elif isinstance(c.l, CList):
                    ret.append(EqC(c.l.elts, CDyn()))
                elif isinstance(c.l, CHTuple):
                    ret.append(EqC(c.l.elts, CDyn()))
                elif isinstance(c.l, CSet):
                    ret.append(EqC(c.l.elts, CDyn()))
                elif isinstance(c.l, CDict):
                    ret += [EqC(c.l.keys, CDyn()), EqC(c.l.values, CDyn())]
                elif isinstance(c.l, CTuple):
                    ret += [EqC(elt, CDyn()) for elt in c.l.elts]
                elif isinstance(c.l, CInstance):
                    pass
                elif isinstance(c.l, CClass):
                    if unsolvable_inherits(c.l, constraints):
                        ret.append(c)
                        continue
                    def st_dyn_class(cls):
                        in_ret = []
                        for fld in cls.fields:
                            in_ret += [EqC(cls.fields[fld], CDyn())]
                        for mem in cls.members:
                            in_ret += [EqC(cls.members[mem], CDyn())]
                        for sup in cls.inherits:
                            in_ret += st_dyn_class(ctbl[sup])
                        return in_ret
                    ret += st_dyn_class(ctbl[c.l.name])
                elif isinstance(c.l, CStructural):
                    ret += [EqC(c.l.members[mem], CDyn()) for mem in c.l.members]
                elif isinstance(c.l, CSubscriptable):
                    ret += [STC(c.l.keys, CDyn()), EqC(c.l.elts, CDyn())]
                elif isinstance(c.l, CPrimitive) or isinstance(c.l, CDyn):
                    pass
                else: raise BailOut(c.l, c.u)
            elif isinstance(c.u, CFunction):
                if isinstance(c.l, CFunction):
                    ret.append(STC(c.l.to, c.u.to))
                    if isinstance(c.l.froms, PosCAT):
                        if isinstance(c.u.froms, PosCAT) and len(c.l.froms.types) == len(c.u.froms.types):
                            ret += [STC(rp, lp) for lp, rp in zip(c.l.froms.types, c.u.froms.types)]
                        elif isinstance(c.u.froms, ArbCAT):
                            ret += [STC(CDyn(), lp) for lp in c.l.froms.types]
                        elif isinstance(c.u.froms, SpecCAT):
                            raise BailOut()
                        else: raise BailOut()
                    elif isinstance(c.l.froms, ArbCAT):
                        if isinstance(c.u.froms, PosCAT):
                            ret += [STC(rp, CDyn()) for rp in c.u.froms.types]
                        elif isinstance(c.u.froms, ArbCAT):
                            pass
                        elif isinstance(c.u.froms, SpecCAT):
                            params = argspec.params(c.u.froms.spec)
                            for u in params:
                                ret.append(STC(u.annotation, CDyn()))
                        else: raise BailOut()
                    elif isinstance(c.l.froms, SpecCAT):
                        if isinstance(c.u.froms, SpecCAT):
                            pairs = argspec.padjoin(c.u.froms.spec, c.l.froms.spec)
                            for u, l in pairs:
                                if u and l and u.name == l.name:
                                    ret.append(STC(u.annotation, l.annotation))
                                else: raise BailOut()
                        elif isinstance(c.u.froms, ArbCAT):
                            params = argspec.params(c.l.froms.spec)
                            for l in params:
                                ret.append(STC(CDyn(), l.annotation))
                        elif isinstance(c.u.froms, PosCAT):
                            try:
                                ba = c.l.froms.spec.bind(*c.u.froms.types)
                            except TypeError:
                                raise BailOut()
                            for param in ba.arguments:
                                arg = ba.arguments[param]
                                _, paramty = argspec.paramty(param, c.l.froms.spec)
                                if isinstance(arg, dict):
                                    for key in arg:
                                        ret += [STC(paramty, arg[key])]
                                elif isinstance(arg, CType):
                                    ret += [STC(paramty, arg)]
                                elif isinstance(arg, tuple):
                                    for elt in arg:
                                        ret += [STC(paramty, elt)]
                                else: raise BailOut(c.l, c.u, arg)
                        else: raise BailOut(c.l, c.u)
                else: raise BailOut(c)
            else: ret += decompose_bivariant(constraints, c, c.l, c.u, ctbl, '<:')
        elif isinstance(c, EqC):
            if isinstance(c.r, CVar) or isinstance(c.r, CVarBind):
                if c.r is not c.l:
                    ret.append(c)
            elif isinstance(c.l, CVar):
                ret.append(c)
            elif isinstance(c.l, CVarBind):
                ret.append(c)
            elif isinstance(c.r, CDyn):
                if isinstance(c.l, CVar):
                    ret.append(c)
                elif isinstance(c.l, CDyn):
                    pass
                else: ret.append(EqC(c.r, c.l))
            elif isinstance(c.r, CFunction):
                if isinstance(c.l, CFunction):
                    ret.append(EqC(c.l.to, c.r.to))
                    if isinstance(c.l.froms, PosCAT):
                        if isinstance(c.r.froms, PosCAT) and len(c.l.froms.types) == len(c.r.froms.types):
                            ret += [EqC(rp, lp) for lp, rp in zip(c.l.froms.types, c.r.froms.types)]
                        elif isinstance(c.r.froms, ArbCAT):
                            ret += [EqC(CDyn(), lp) for lp in c.l.froms.types]
                        # elif isinstance(c.r.froms, VarCAT):
                        #     ret.append(EqC(c.l.froms, c.r.froms))
                        else: raise BailOut(c.r)
                    elif isinstance(c.l.froms, ArbCAT):
                        if isinstance(c.r.froms, PosCAT):
                            ret += [EqC(rp, CDyn()) for rp in c.r.froms.types]
                        elif isinstance(c.r.froms, ArbCAT):
                            pass
                        else: raise BailOut()
                    elif isinstance(c.l.froms, SpecCAT):
                        if isinstance(c.r.froms, SpecCAT):
                            param_pairs = argspec.padjoin(c.l.froms.spec,
                                                          c.r.froms.spec)
                            for lp, rp in param_pairs:
                                if lp and rp:
                                    ret.append(EqC(lp.annotation, rp.annotation))
                        elif isinstance(c.r.froms, ArbCAT):
                            for k in c.l.froms.spec.parameters:
                                ret.append(EqC(c.l.froms.spec.parameters[k].annotation, CDyn()))
                        elif isinstance(c.r.froms, PosCAT):
                            try:
                                ba = c.l.froms.spec.bind(*c.r.froms.types)
                                for param in ba.arguments:
                                    arg = ba.arguments[param]
                                    _, paramty = argspec.paramty(param, c.l.froms.spec)
                                    if isinstance(arg, dict):
                                        for key in arg:
                                            ret += [STC(arg[key], paramty)]
                                    elif isinstance(arg, CType):
                                        ret += [STC(arg, paramty)]
                                    elif isinstance(arg, tuple):
                                        for elt in arg:
                                            ret += [STC(elt, paramty)]
                                    else: raise BailOut(c.l, c.r, arg)
                            except TypeError:
                                raise BailOut()
                        else: raise BailOut()
                    # elif isinstance(c.l.froms, VarCAT):
                    #     if isinstance(c.r.froms, VarCAT):
                    #         ret.append(EqC(c.l.froms, c.r.froms))
                    #     else:
                    #         raise BailOut()
                    else: raise BailOut(c.r, c.l, type(c.r.froms), type(c.l.froms))
                elif isinstance(c.l, CDyn):
                    ret.append(EqC(CDyn(), c.r.to))
                    if isinstance(c.r.froms, PosCAT):
                        ret += [EqC(CDyn(), rp) for rp in c.r.froms.types]
                    elif isinstance(c.r.froms, ArbCAT):
                        pass
                    elif isinstance(c.r.froms, SpecCAT):
                        params = argspec.params(c.r.froms.spec)
                        for r in params:
                            ret.append(EqC(CDyn(), r.annotation))
                    else: raise BailOut()
                elif isinstance(c.l, CClass):
                    if unsolvable_inherits(c.l, constraints):
                        ret.append(c)
                        continue
                    if ctbl[c.l.name].supports('__init__', ctbl):
                        init = CFunction(ctbl[c.l.name].lookup('__init__', ctbl).bind().froms, CInstance(c.l.name))
                        ret.append(EqC(init, c.r))
                    else: raise BailOut()
                else: raise BailOut(c.l, c.r)
            else: ret += decompose_bivariant(constraints, c, c.l, c.r, ctbl, '=')
        elif isinstance(c, CheckC):
            if unsolvable_inherits(c.l, constraints):
                ret.append(c)
                continue
            matchcode = match(c.l, c.s, ctbl)
            #print(c, matchcode)
            if matchcode == CONFIRM:
                ret.append(EqC(c.l, c.r))
            elif matchcode == PENDING:
                ret.append(c)
            elif matchcode == DENY or matchcode == UNCONFIRM:
                ret += [EqC(part, CDyn()) for part in c.r.parts(ctbl)]
        else:
            ret.append(c)
    return ret
                    
                    

def intlike(l):
    return isinstance(l, CInt) or isinstance(l, CSingletonInt) or isinstance(l, CBool)

def floatlike(l):
    return isinstance(l, CFloat) or isinstance(l, CInt) or isinstance(l, CSingletonInt) or isinstance(l, CBool)
                
def prop_constraints(fn):
    def inner(*args, **kwargs):
        ret = fn(*args, **kwargs)
        if not isinstance(ret, tuple):
            return ret, []
        else: return ret
    return inner

@prop_constraints
def binop_solve(l, op, r):
    from ..consistency import getop

    if isinstance(l, CDyn):
        return CDyn()
    elif (not isinstance(op, ast.Mod) or not isinstance(l, CStr))\
         and isinstance(r, CDyn): # If LHS is a string and op is %, then we def have a string
        return CDyn()
    if isinstance(op, ast.Add):
        if isinstance(l, CSingletonInt) and isinstance(r, CSingletonInt):
            return CSingletonInt(l.n + r.n)
        elif intlike(l) and intlike(r):
            return CInt()
        elif floatlike(l) and floatlike(r):
            return CFloat()
        elif isinstance(l, CStr) and isinstance(r, CStr):
            return CStr()
        elif isinstance(l, CList) and isinstance(r, CList):
            return l, [EqC(l.elts, r.elts)]
        elif isinstance(l, CHTuple) and isinstance(r, CHTuple):
            return l, [EqC(l.elts, r.elts)]
        elif isinstance(l, CTuple) and isinstance(r, CTuple):
            return CTuple(*(l.elts + r.elts))
        else: 
            raise BailOut(l, op, r)
    elif isinstance(op, ast.Sub) or isinstance(op, ast.Pow): # These ones can take floats
        if isinstance(l, CSingletonInt) and isinstance(r, CSingletonInt):
            return CSingletonInt(getop(op)(l.n, r.n))
        elif intlike(l) and intlike(r):
            return CInt()
        elif floatlike(l) and floatlike(r):
            return CFloat()
        else: 
            raise BailOut()
    elif isinstance(op, ast.Div):
        if floatlike(l) and floatlike(r):
            return CFloat()
        else: 
            raise BailOut()
    elif isinstance(op, ast.FloorDiv): # Takes floats, but always return int
        if isinstance(l, CSingletonInt) and isinstance(r, CSingletonInt):
            return CSingletonInt(getop(op)(l.n, r.n))
        elif floatlike(l) and floatlike(r):
            return CInt()
        else: 
            raise BailOut()
    elif isinstance(op, ast.LShift) or isinstance(op, ast.RShift) or \
         isinstance(op, ast.BitOr) or isinstance(op, ast.BitXor) or isinstance(op, ast.BitAnd): # These ones cant
        if isinstance(l, CSingletonInt) and isinstance(r, CSingletonInt):
            return CSingletonInt(getop(op)(l.n, r.n))
        elif intlike(l) and intlike(r):
            return CInt()
        else: 
            raise BailOut()
    elif isinstance(op, ast.Mod): # Can take floats
        if isinstance(l, CSingletonInt) and isinstance(r, CSingletonInt):
            return CSingletonInt(getop(op)(l.n, r.n))
        elif intlike(l) and intlike(r):
            return CInt()
        elif floatlike(l) and floatlike(r):
            return CFloat()
        elif isinstance(l, CStr):
            return CStr()
        else: 
            raise BailOut()
    elif isinstance(op, ast.Mult): # Can take floats
        if isinstance(l, CSingletonInt) and isinstance(r, CSingletonInt):
            return CSingletonInt(getop(op)(l.n, r.n))
        elif intlike(l) and intlike(r):
            return CInt()
        elif floatlike(l) and floatlike(r):
            return CFloat()
        if isinstance(l, CStr) and intlike(r):
            return CStr()
        if intlike(l) and isinstance(r, CStr):
            return CStr()
        if isinstance(l, CList) and intlike(r):
            return l
        if intlike(l) and isinstance(r, CList):
            return r
        else: 
            raise BailOut()
    else:
        raise InternalReticulatedError(op)

    
@prop_constraints
def unop_solve(op, o):
    if isinstance(o, CDyn):
        return CDyn()
    elif isinstance(op, ast.Not):
        return CBool()
    elif isinstance(op, ast.Invert):
        if isinstance(o, CSingletonInt):
            return CSingletonInt(~ o.n)
        elif intlike(o): 
            return CInt()
        else:
            raise BailOut()
    elif isinstance(op, ast.UAdd) or isinstance(op, ast.USub):
        if isinstance(o, CSingletonInt):
            return CSingletonInt(o.n if isinstance(op, ast.UAdd) else -o.n)
        elif intlike(o): #yes float
            return CInt()
        elif floatlike(o): 
            return CFloat()
        else:
            raise BailOut()

