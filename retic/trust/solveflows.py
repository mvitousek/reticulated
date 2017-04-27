from .. import retic_ast, exc, typing
from . import variables
import ast

initial_bindings = {}

flowlog = []
bottom = []

trackflows = False

def new_flow(l, r):
    if trackflows:
        flowlog.append((l, r))

def fail(msg):
    if trackflows:
        bottom.append(msg)

def append_elt(map, k, v):
    if k in map:
        map[getvar(k)].append(v)
    else: map[getvar(k)] = [v]

def isvar(k):
    return (isinstance(k, retic_ast.Trusted) and isinstance(k.type, retic_ast.FlowVariable)) or \
        isinstance(k, variables.FlowVariableID)

def getvar(k):
    if isinstance(k, retic_ast.FlowVariable):
        return k.var
    elif isinstance(k, retic_ast.Trusted) and isinstance(k.type, retic_ast.FlowVariable):
        return k.type.var
    else: return k

def stripvar(k):
    if isinstance(k, retic_ast.FlowVariable):
        return stripvar(k.type)
    else: return k

def primitive(k):
    if isinstance(k, retic_ast.Trusted):
        return primitive(k.type)
    return isinstance(k, retic_ast.Primitive)

def computeclosure(allflows, processflows):
    def fpull(l1, r1, l2, r2):
        if isvar(r1) and isvar(l2) and isvar(r2) and getvar(r1) == getvar(l2) and iskind(l1, r1):
            if moreprec(initial_bindings[getvar(r2)], l1) or not isinstance(l2, retic_ast.Trusted):
                print('fpull')
                return [(l1, r2)]
            else: 
                print('fpull nope', l1, r1, r2, initial_bindings[getvar(r2)])
                return []
        else: return []
    def ffactor(l, r):
        if isvar(r) and not isvar(l) and not primitive(l):
            kl = kind(l, r)
            if kl == l:
                return []
            print('ffactor', [(l, kl), (kl, r)])
            return [(l, kl), (kl, r)]
        else: return []
    def ftrans(l1, r1, l2, r2):
        if isvar(r1) and isvar(l2) and iskind(l1, r1) and getvar(r1) == getvar(l2) and dyncon(l1, r2):
            print('ftrans')
            return [(l1, r2)]
        else: return []
    def fexpfunl(l, r):
        if isinstance(l, retic_ast.Dyn) and isinstance(r, retic_ast.Function):
            if isinstance(r.froms, retic_ast.PosAT):
                fn = retic_ast.Function(retic_ast.PosAT([retic_ast.Dyn() for _ in r.froms.types]),
                                        retic_ast.Dyn())
            else: raise exc.UnimplementedException(r.froms)
            
            print('fexpfunl')
            return [(fn, r)]
        else: return []
    def fexpfunr(l, r):
        if isinstance(r, retic_ast.Dyn) and isinstance(l, retic_ast.Function):
            if isinstance(l.froms, retic_ast.PosAT):
                fn = retic_ast.Function(retic_ast.PosAT([retic_ast.Dyn() for _ in l.froms.types]),
                                        retic_ast.Dyn())
            else: raise exc.UnimplementedException(l.froms)
            
            print('fexpfunr')
            return [(l, fn)]
        else: return []
    def fexplistl(l, r):
        if isinstance(l, retic_ast.Dyn) and isinstance(r, retic_ast.List):
            fn = retic_ast.List(retic_ast.Dyn())
            print('fexplistl')
            return [(fn, r)]
        else: return []
    def fexplistr(l, r):
        if isinstance(r, retic_ast.Dyn) and isinstance(l, retic_ast.List):
            fn = retic_ast.List(retic_ast.Dyn())
            print('fexplistr')
            return [(r, fn)]
        else: return []
    def fsplitfun(l, r):
        if isinstance(l, retic_ast.Function) and isinstance(r, retic_ast.Function):
            if isinstance(l.froms, retic_ast.PosAT) and isinstance(r.froms, retic_ast.PosAT):
                if len(l.froms.types) == len(r.froms.types):
                    print('fsplitfun')
                    return [(getvar(rn), getvar(ln)) for (ln, rn) in zip(l.froms.types, r.froms.types)] + [(getvar(l.to), getvar(r.to))]
                else: return []
            else: raise exc.UnimplementedException(l.froms, r.froms)
        else: return []
    def fsplitlist(l, r):
        if isinstance(l, retic_ast.List) and isinstance(r, retic_ast.List):
            print('fsplitlist')
            return [(getvar(l.elts), getvar(r.elts)), (getvar(r.elts), getvar(l.elts))]
        else: return []
    def ftrust(l, r):
        if isinstance(l, retic_ast.Trusted) and isinstance(l.type, retic_ast.FlowVariable) and isvar(r):
            print('ftrust')
            return [(retic_ast.Trusted(l.type.type), r)]
        else: return []

    newflows = []
    for l, r in processflows:
        newflows += ffactor(l, r)
        newflows += fexpfunl(l, r)
        newflows += fexpfunr(l, r)
        newflows += fsplitfun(l, r)
        newflows += fexplistl(l, r)
        newflows += fexplistr(l, r)
        newflows += fsplitlist(l, r)
        newflows += ftrust(l, r)
        for l2, r2 in allflows:
            if l is not l2 or r is not r2: 
                newflows += ftrans(l, r, l2, r2) + ftrans(l2, r2, l, r)
                newflows += fpull(l, r, l2, r2) + fpull(l2, r2, l, r)
    newflows = [(l, r) for (l, r) in newflows if l != r and (l, r) not in allflows]
    if newflows:
        print('New Flows!!!!!\n\n', newflows)
        return computeclosure(allflows + newflows, newflows)
    return allflows

def fix(flows, fixed):
    def fixh(f):
        if isinstance(f, retic_ast.FlowVariable):
            if f.var in fixed:
                return fixed[f.var]
            return f
        elif isinstance(f, variables.FlowVariableID):
            if f in fixed:
                return fixed[f]
            return f
        elif isinstance(f, retic_ast.Trusted):
            return retic_ast.Trusted(fixh(f.type))
        elif isinstance(f, retic_ast.Function):
            if isinstance(f.froms, retic_ast.PosAT):
                return retic_ast.Function(retic_ast.PosAT([fixh(a) for a in f.froms.types]), fixh(f.to))
            else:
                raise exc.UnimplementedException(f.froms)
        elif isinstance(f, retic_ast.List):
            return retic_ast.List(fixh(f.elts))
        else:
            return f
    return [(fixh(l), fixh(r)) for (l,r) in flows]

def solve(fixed=None):
    if fixed is None:
        fixed = {}
    if bottom:
        print('Flow solver failed:', *bottom, sep='\n')
        return {}
    tflows = fix(flowlog, fixed)
    print('FLOWS:\n', tflows)
    closedflows = computeclosure(tflows, tflows)
    print('FINAL FLOWS', *['{} -> {}'.format(l, r) for (l, r) in closedflows], sep='\n', end='\n\n')

    intoflows = {}
    
    for l, r, in closedflows:
        if isvar(r) and not isvar(l):
            append_elt(intoflows, r, l)
        

    solution = {}
    for k in intoflows:
        ksol, newfix = var_solution(k, intoflows)
        if ksol is not None:
            solution[k] = ksol
        elif newfix is not None:
            allfixes = fixed.copy()
            allfixes.update(newfix)
            print ('RESTARTING')
            return solve(fixed=allfixes)

    return solution

# I(X)
def var_solution(x, intoflows):
    print('Solving', x)
    intox = into(x, intoflows)
    if len(intox) == 0:
        return None, None

    join, intox = kind(intox[0], x), intox[1:]
    print(join)
    for k in intox:
        print(kind(k, x))
        join = lub(join, kind(k, x))

    sol = type_solution(join)
    
    if not moreprec(initial_bindings[x], sol):
        print ('Bad solution', sol, 'instead using', initial_bindings[x])
        return initial_bindings[x], None
    else:
        print ('Solution', sol)
        return sol, None

# I^(X)
def type_solution(x):
    return x

# T+(X)
def into(x, intoflows):
    return intoflows[getvar(x)]

def lub(k1, k2):
    if isinstance(k1, retic_ast.Dyn):
        return k1
    elif isinstance(k2, retic_ast.Dyn):
        return k2
    if isinstance(k1, retic_ast.Trusted):
        if isinstance(k2, retic_ast.Trusted):
            if k1.type == k2.type:
                return k1
            elif isinstance(k1.type, retic_ast.SingletonInt) and isinstance(k2.type, retic_ast.Int):
                return retic_ast.Trusted(retic_ast.Int())
            elif isinstance(k2.type, retic_ast.SingletonInt) and isinstance(k1.type, retic_ast.Int):
                return retic_ast.Trusted(retic_ast.Int())
            else:
                return trust(lub(k1.type, k2.type))
        else: return lub(k1.type, k2)
    elif isinstance(k2, retic_ast.Trusted):
        return lub(k1, k2.type)
    elif isinstance(k1, retic_ast.List):
        if isinstance(k2, retic_ast.List):
            return k1
        else:
            return retic_ast.Dyn()
    elif isinstance(k1, retic_ast.Function):
        if isinstance(k2, retic_ast.Function):
            if isinstance(k1.froms, retic_ast.PosAT):
                if isinstance(k2.froms, retic_ast.PosAT):
                    if len(k1.froms.types) == len(k2.froms.types):
                        return k1
                    else: return retic_ast.Dyn()
                else: return retic_ast.Dyn()
            else: return retic_ast.Dyn()
        else: return retic_ast.Dyn()
    elif isinstance(k2, retic_ast.Function):
        return retic_ast.Dyn()
    elif isinstance(k1, retic_ast.SingletonInt) and isinstance(k2, retic_ast.Int):
        return retic_ast.Int()
    elif isinstance(k2, retic_ast.SingletonInt) and isinstance(k1, retic_ast.Int):
        return retic_ast.Int()
    elif k1 == k2:
        return k1
    else: return retic_ast.Dyn()
    

# ||T||x
def kind(t, x):
    if isinstance(t, retic_ast.Dyn):
        return t
    elif isinstance(t, retic_ast.Trusted):
        return retic_ast.Trusted(kind(t.type, x))
    elif isinstance(t, retic_ast.Primitive):
        return t
    elif isinstance(t, retic_ast.Function):
        if isinstance(t.froms, retic_ast.PosAT):
            return retic_ast.Function(retic_ast.PosAT([retic_ast.FlowVariable(stripvar(arg), variables.PosArgVar(x, n)) for \
                                                       n, arg in enumerate(t.froms.types)]),
                                      retic_ast.FlowVariable(stripvar(t.to), variables.RetVar(x)))
        else: raise exc.UnimplementedException(t.froms)
    elif isinstance(t, retic_ast.List):
        return retic_ast.List(retic_ast.FlowVariable(stripvar(t.elts), variables.ListEltVar(x)))
    else: raise exc.UnimplementedException(t)

def iskind(t, x):
    if isinstance(t, variables.FlowVariableID):
        return False
    elif isinstance(t, retic_ast.Dyn):
        return True
    elif isinstance(t, retic_ast.Trusted):
        return iskind(getvar(t.type), x)
    elif isinstance(t, retic_ast.Primitive):
        return True
    elif isinstance(t, retic_ast.Function):
        if isinstance(t.froms, retic_ast.PosAT):
            return t.froms == [retic_ast.FlowVariable(stripvar(arg), variables.PosArgVar(x, n)) for \
                               n, arg in enumerate(t.froms.types)] and \
                t.to == retic_ast.FlowVariable(stripvar(t.to), variables.RetVar(x))
        else: raise exc.UnimplementedException(t.froms)
    elif isinstance(t, retic_ast.List):
        return t == retic_ast.List(retic_ast.FlowVariable(stripvar(t.elts), variables.ListEltVar(x)))
    else: raise exc.UnimplementedException(t)

def dyncon(l, r):
    if isvar(l) or isvar(r):
        return False
    elif isinstance(l, retic_ast.Dyn) or isinstance(r, retic_ast.Dyn):
        return True
    elif isinstance(l, retic_ast.Primitive) and isinstance(r, retic_ast.Primitive):
        from .. import consistency
        return consistency.consistent(l, r)
    elif isinstance(l, retic_ast.Function) and isinstance(r, retic_ast.Function):
        if isinstance(l.froms, retic_ast.PosAT) and isinstance(r.froms, retic_ast.PosAT):
            if len(l.froms.types) == len(r.froms.types):
                return True
            else: return False
        else: raise exc.UnimplementedException(l.froms, r.froms)
    elif isinstance(l, retic_ast.List) and isinstance(r, retic_ast.List):
        return True
    else: return False


def subflows(var, type):
    if isinstance(type, retic_ast.List):
        nvar = variables.ListEltVar(var)
        initial_bindings[nvar] = type.elts
        return retic_ast.List(retic_ast.FlowVariable(subflows(nvar, type.elts), nvar))
    elif isinstance(type, retic_ast.Function):
        if isinstance(type.froms, retic_ast.PosAT):
            nfroms = []
            for n, arg in enumerate(type.froms.types):
                nvar = variables.PosArgVar(var, n)
                narg = subflows(nvar, arg)
                initial_bindings[nvar] = arg
                nfroms.append(retic_ast.FlowVariable(narg, nvar))
            rvar = variables.RetVar(var)
            initial_bindings[rvar] = type.to
            return retic_ast.Function(retic_ast.PosAT(nfroms),
                                      retic_ast.FlowVariable(subflows(rvar, type.to),
                                                             rvar))
        else:
            fail('Cannot infer trust for non-positional argument function annotations')
            return type
    elif isinstance(type, retic_ast.Primitive):
        return type
    elif isinstance(type, retic_ast.Dyn):
        return type
    else:
        return type
        bottom.append('Cannot infer trust for ' + str(type))
    
def handleable_args(args: typing.List[ast.expr], keywords: typing.List[ast.keyword], starargs, kwargs):
    return not (keywords or starargs or kwargs)

def moreprec(orig, new):
    if isinstance(orig, retic_ast.FlowVariable):
        return moreprec(orig.type, new)
    elif isinstance(new, retic_ast.FlowVariable):
        return moreprec(orig, new.type)
    elif isinstance(new, retic_ast.Dyn):
        return False
    elif isinstance(orig, retic_ast.Dyn):
        return True
    elif isinstance(new, retic_ast.Trusted):
        return moreprec(orig, new.type)
    elif isinstance(new, retic_ast.SingletonInt):
        return new == orig or isinstance(orig, retic_ast.Int)
    elif isinstance(new, retic_ast.Primitive):
        return new == orig
    elif isinstance(new, retic_ast.List):
        return isinstance(orig, retic_ast.List)
    elif isinstance(new, retic_ast.Function):
        if isinstance(orig, retic_ast.Function):
            return True
            # if isinstance(new.froms, retic_ast.PosAT) and \
            #    isinstance(orig.froms, retic_ast.PosAT):
            #     return all(moreprec(o, n) for (o, n) in zip(orig.froms.types, new.froms.types)) and \
            #         moreprec(orig.to, new.to)
            # else: raise exc.UnimplementedException(new.froms, orig.froms)
        else: return False
    else: return False


def trust(t):
    if isinstance(t, retic_ast.Dyn):
        return t
    elif isinstance(t, retic_ast.Trusted):
        return t
    elif isinstance(t, retic_ast.FlowVariable) and isinstance(t.type, retic_ast.Dyn):
        return t
    else: return retic_ast.Trusted(t)
