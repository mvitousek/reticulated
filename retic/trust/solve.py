from .constraints import *
from .ctypes import *
from .. import retic_ast

def normalize(constraints):
    oc = None
    while oc != constraints:
        oc = constraints
        constraints = decompose(constraints)
    print(constraints)
    for c in constraints:
        if isinstance(c, EqC) and isinstance(c.l, CVar) and c.l is not c.r:
            new_constraints = [old_c.subst(c.l, c.r) for old_c in constraints]
            print('Substituting', c.l.name, 'to', c.r)
            return normalize(new_constraints + [DefC(c.l, c.r)])
        elif isinstance(c, EqC) and isinstance(c.r, CVar):
            return normalize(constraints + [EqC(c.r, c.l)])
    vars = sum([c.vars() for c in constraints], [])
    def type_lower_bound(v, c):
        return isinstance(c, STC) and c.u is v and not isinstance(c.l, CVar) and v not in c.l.vars()
    for v in vars:
        cprime = [c for c in constraints if not type_lower_bound(v, c)]
        if all([c.solvable(v) for c in cprime]):
            lbs = [c for c in constraints if type_lower_bound(v, c)]
            if len(lbs) == 0:
                join = CDyn()
            else:
                if all(isinstance(lb.l, type(lbs[0].l)) for lb in lbs):
                    join = lbs[0].l
                else:
                    join = CDyn()
            print('Solving', v.name, 'at', join)
            return normalize(constraints + [EqC(v, join)])
    return constraints

def decompose_bivariant(l, r):
    ret = []
    assert not (isinstance(r, CVar) or isinstance(r, CDyn) or isinstance(r, CFunction)), (l, r)
    if isinstance(r, CList):
        if isinstance(l, CList):
            ret.append(EqC(l.elts, r.elts))
        elif isinstance(l, CSubscriptable):
            ret += [EqC(l.keys, CInt()), EqC(l.elts, r.elts)]
        else: raise Exception()
    elif isinstance(r, CHTuple):
        if isinstance(l, CHTuple):
            ret.append(EqC(l.elts, r.elts))
        elif isinstance(l, CSubscriptable):
            ret += [EqC(l.keys, CInt()), EqC(l.elts, r.elts)]
        else: raise Exception()
    elif isinstance(r, CSet):
        if isinstance(l, CSet):
            ret.append(EqC(l.elts, r.elts))
        else: raise Exception()
    elif isinstance(r, CDict):
        if isinstance(l, CDict):
            ret.append(EqC(l.keys, r.keys))
            ret.append(EqC(l.values, r.values))
        elif isinstance(l, CSubscriptable):
            ret += [EqC(l.keys, r.keys), EqC(l.elts, r.keys)]
        else: raise Exception()
    elif isinstance(r, CTuple):
        if isinstance(l, CTuple) and len(l.elts) == len(r.elts):
            ret += [EqC(le, re) for le, re in zip(l.elts, r.elts)]
        elif isinstance(l, CSubscriptable):
            ret += [EqC(r.keys, CInt()), EqC(l.elts, CDyn())] + [EqC(elt, CDyn()) for elt in r.elts]
        else: raise Exception()
    elif isinstance(r, CInstance):
        raise Exception()
    elif isinstance(r, CClass):
        raise Exception()
    elif isinstance(r, CStructural):
        if isinstance(l, CStructural):
            ret += [EqC(l.members[mem], r.members[mem]) for mem in l.members if mem in r.members]
            # We may need to set members not in the intersect to dyn
        else: raise Exception()
    elif isinstance(r, CPrimitive):
        if isinstance(l, CPrimitive):
            pass
        else: raise Exception()
    elif isinstance(r, CSubscriptable): # This may be able to be refined to subtyping in some cases if it goes back in decompose
        if isinstance(l, CSubscriptable):
            ret += [EqC(r.keys, l.keys), EqC(l.elts, r.elts)]
        elif isinstance(l, CList):
            ret += [EqC(r.keys, CInt()), EqC(l.elts, r.elts)]
        elif isinstance(l, CHTuple):
            ret += [EqC(r.keys, CInt()), EqC(l.elts, r.elts)]
        elif isinstance(l, CTuple): # With check constraints maybe we can do something here
            ret += [EqC(r.keys, CInt()), EqC(r.elts, CDyn())] + [EqC(elt, CDyn()) for elt in l.elts]
        elif isinstance(l, CDict):
            ret += [EqC(r.keys, l.keys), EqC(l.values, r.elts)]
    else: raise Exception()
    return ret


def decompose(constraints):
    ret = []
    for c in constraints:
        if isinstance(c, STC):
            if isinstance(c.u, CVar):
                if c.u is not c.l:
                    ret.append(c)
            elif isinstance(c.l, CVar):
                ret.append(c)
            elif isinstance(c.u, CDyn):
                if isinstance(c.l, CVar):
                    ret.append(c)
                elif isinstance(c.l, CFunction):
                    ret.append(STC(c.l.to, CDyn()))
                    if isinstance(c.l.froms, PosCAT):
                        ret += [STC(CDyn(), param) for param in c.l.froms.types]
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
                    raise Exception()
                elif isinstance(c.l, CClass):
                    raise Exception()
                elif isinstance(c.l, CStructural):
                    ret += [EqC(c.l.members[mem], CDyn()) for mem in c.l.members]
                elif isinstance(c.l, CPrimitive) or isinstance(c.l, CDyn):
                    pass
                else: raise Exception()
            elif isinstance(c.u, CFunction):
                if isinstance(c.l, CFunction):
                    ret.append(STC(c.l.to, c.u.to))
                    if isinstance(c.l.froms, PosCAT):
                        if isinstance(c.u.froms, PosCAT) and len(c.l.froms.types) == len(c.u.froms.types):
                            ret += [STC(rp, lp) for lp, rp in zip(c.l.froms.types, c.u.froms.types)]
                        elif isinstance(c.u.froms, ArbCAT):
                            ret += [STC(CDyn(), lp) for lp in c.l.froms.types]
                        else: raise Exception()
                    elif isinstance(c.l.froms, ArbCAT):
                        if isinstance(c.u.froms, PosCAT):
                            ret += [STC(rp, CDyn()) for rp in c.u.froms.types]
                        elif isinstance(c.u.froms, ArbCAT):
                            pass
                        else: raise Exception()
                    else: raise Exception()
                else: raise Exception()
            else: ret += decompose_bivariant(c.l, c.u)
        elif isinstance(c, EqC):
            if isinstance(c.r, CVar):
                if c.r is not c.l:
                    ret.append(c)
            elif isinstance(c.l, CVar):
                ret.append(c)
            elif isinstance(c.r, CDyn):
                if isinstance(c.l, CVar):
                    ret.append(c)
                elif isinstance(c.l, CDyn):
                    pass
                else: raise Exception()
            elif isinstance(c.r, CFunction):
                if isinstance(c.l, CFunction):
                    ret.append(EqC(c.l.to, c.r.to))
                    if isinstance(c.l.froms, PosCAT):
                        if isinstance(c.r.froms, PosCAT) and len(c.l.froms.types) == len(c.r.froms.types):
                            ret += [EqC(rp, lp) for lp, rp in zip(c.l.froms.types, c.r.froms.types)]
                        elif isinstance(c.r.froms, ArbCAT):
                            ret += [EqC(CDyn(), lp) for lp in c.l.froms.types]
                        else: raise Exception()
                    elif isinstance(c.l.froms, ArbCAT):
                        if isinstance(c.r.froms, PosCAT):
                            ret += [EqC(rp, CDyn()) for rp in c.r.froms.types]
                        elif isinstance(c.r.froms, ArbCAT):
                            pass
                        else: raise Exception()
                    else: raise Exception()
                else: raise Exception()
            else: ret += decompose_bivariant(c.l, c.r)
        elif isinstance(c, CheckC):
            try:
                matched = ctype_match(c.l, c.s)
                if matched is c.l:
                    ret.append(EqC(c.l, c.r))
                else:
                    ret.append(c)
            except NoMatch:
                ret += [EqC(part, CDyn()) for part in c.r.parts()]
        else:
            ret.append(c)
    return ret
                    
                    
                
