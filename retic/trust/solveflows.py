from .. import retic_ast, exc, typing
from . import variables, varinsertion
import ast

initial_bindings = {}

flowlog = []
bottom = []

def debugprint(*args, **kwargs):
    #print(*args, **kwargs)
    pass
    
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
        isinstance(k, retic_ast.FlowVariable) or \
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
        if not isvar(l1) and isvar(r1) and isvar(l2) and isvar(r2) and getvar(r1) == getvar(l2) and iskind(l1, r1):
            if not isinstance(l2, retic_ast.Trusted) or getvar(r2) not in initial_bindings or moreprec(initial_bindings[getvar(r2)], l1):
                debugprint('fpull')
                return [(l1, r2)]
            else: 
                debugprint('fpull nope', l1, r1, r2, initial_bindings[getvar(r2)])
                return []
        else: 
            debugprint('fpull nope!', l1, r1, l2, r2, iskind(l1, r1))
            return []
    def ffactor(l, r):
        if isvar(r) and not isvar(l) and not primitive(l):
            kl = kind(l, r)
            if kl == l:
                debugprint('ffactor nope?', kl == l, kl, l)
                return []
            debugprint('ffactor', [(l, kl), (kl, r)])
            return [(l, kl), (kl, r)]
        else: 
            debugprint('ffactor nope', [l, r])
            return []
    def ftrans(l1, r1, l2, r2):
        if isvar(r1) and isvar(l2) and getvar(r1) == getvar(l2) and dyncon(l1, r2) and iskind(l1, r1):
            debugprint('ftrans')
            return [(l1, r2)]
        else: return []
    def fexpfunl(l, r):
        if isinstance(l, retic_ast.Dyn) and isinstance(r, retic_ast.Function):
            if isinstance(r.froms, retic_ast.PosAT):
                fn = retic_ast.Function(retic_ast.PosAT([retic_ast.Dyn() for _ in r.froms.types]),
                                        retic_ast.Dyn())
            else: raise exc.UnimplementedException(r.froms)
            
            debugprint('fexpfunl')
            return [(fn, r)]
        else: return []
    def fexpfunr(l, r):
        if isinstance(r, retic_ast.Dyn) and isinstance(l, retic_ast.Function):
            if isinstance(l.froms, retic_ast.PosAT):
                fn = retic_ast.Function(retic_ast.PosAT([retic_ast.Dyn() for _ in l.froms.types]),
                                        retic_ast.Dyn())
            else: raise exc.UnimplementedException(l.froms)
            
            debugprint('fexpfunr')
            return [(l, fn)]
        else: return []
    def fexplistl(l, r):
        if isinstance(l, retic_ast.Dyn) and isinstance(r, retic_ast.List):
            fn = retic_ast.List(retic_ast.Dyn())
            debugprint('fexplistl')
            return [(fn, r)]
        else: return []
    def fexplistr(l, r):
        if isinstance(r, retic_ast.Dyn) and isinstance(l, retic_ast.List):
            fn = retic_ast.List(retic_ast.Dyn())
            debugprint('fexplistr')
            return [(r, fn)]
        else: return []
    def fsplitfun(l, r):
        if isinstance(l, retic_ast.Trusted):
            l = l.type
        if isinstance(r, retic_ast.Trusted):
            r = r.type
        if isinstance(l, retic_ast.Function) and isinstance(r, retic_ast.Function):
            if isinstance(l.froms, retic_ast.PosAT) and isinstance(r.froms, retic_ast.PosAT):
                if len(l.froms.types) == len(r.froms.types):
                    debugprint('fsplitfun')
                    return [(getvar(rn), getvar(ln)) for (ln, rn) in zip(l.froms.types, r.froms.types)] + [(getvar(l.to), getvar(r.to))]
                else: return []
            else: raise exc.UnimplementedException(l.froms, r.froms)
        else: return []
    def fsplitlist(l, r):
        if isinstance(l, retic_ast.Trusted):
            l = l.type
        if isinstance(r, retic_ast.Trusted):
            r = r.type
        if isinstance(l, retic_ast.List) and isinstance(r, retic_ast.List):
            debugprint('fsplitlist')
            return [(getvar(l.elts), getvar(r.elts)), (getvar(r.elts), getvar(l.elts))]
        else: return []
    def fsplitinstancel(l, r):
        if isinstance(l, retic_ast.Trusted):
            l = l.type
        if isinstance(l, retic_ast.Instance) and isvar(r):
            if getvar(r) in variables.members and variables.members[getvar(r)]:
                debugprint('fsplitinstancel')
                return sum(([(getvar(l[k.key]), k), (k, getvar(l[k.key]))] for k in variables.members[getvar(r)]), [])
            else:
                debugprint('fsplitinstancel no', r)
                return []
        else: return []
    def fsplitinstancer(l, r):
        if isinstance(r, retic_ast.Trusted):
            r = r.type
        if isinstance(r, retic_ast.Instance) and isvar(l) and getvar(l) in variables.members and variables.members[getvar(l)]:
            debugprint('fsplitinstancer')
            return sum(([(getvar(r[k.key]), k), (k, getvar(r[k.key]))] for k in variables.members[getvar(l)]), [])
        else: return []
    def ftrust(l, r):
        if isinstance(l, retic_ast.Trusted) and isinstance(l.type, retic_ast.FlowVariable) and isvar(r):
            debugprint('ftrust')
            return [(retic_ast.Trusted(l.type.type), r)]
        else: return []

    newflows = []
    for l, r in filter_unhandled(processflows):
        newflows += ffactor(l, r)
        newflows += fexpfunl(l, r)
        newflows += fexpfunr(l, r)
        newflows += fsplitfun(l, r)
        newflows += fexplistl(l, r)
        newflows += fexplistr(l, r)
        newflows += fsplitlist(l, r)
        newflows += fsplitinstancel(l, r)
        newflows += fsplitinstancer(l, r)
        newflows += ftrust(l, r)
        for l2, r2 in allflows:
            if l is not l2 or r is not r2: 
                newflows += ftrans(l, r, l2, r2) + ftrans(l2, r2, l, r)
                newflows += fpull(l, r, l2, r2) + fpull(l2, r2, l, r)
    newflows = [(l, r) for (l, r) in newflows if l != r and (l, r) not in allflows]
    if newflows:
        debugprint('New Flows!!!!!\n\n', newflows)
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

def filter_unhandled(log):
    def unhandled(k):
        if isinstance(k, retic_ast.Trusted) or isinstance(k, retic_ast.FlowVariable):
            return unhandled(k.type)
        elif isinstance(k, retic_ast.Function):
            if isinstance(k.froms, retic_ast.NamedAT):
                return True
        elif isinstance(k, retic_ast.Tuple):
            return True
        return False
    res = []
    for l, r in log:
        if unhandled(l):
            if not unhandled(r):
                res.append((retic_ast.Dyn(), r))
        elif unhandled(r):
            res.append((l, retic_ast.Dyn()))
        else:
            res.append((l, r))
    return res
        

def solve(fixed=None):
    if fixed is None:
        fixed = {}
    if bottom:
        debugprint('Flow solver failed:', *bottom, sep='\n')
        return {}
    
    filtered_flows = filter_unhandled(flowlog)
    
    tflows = fix(filtered_flows, fixed)
    debugprint('FLOWS:\n', tflows)
    closedflows = computeclosure(tflows, tflows)
    debugprint('FINAL FLOWS', *['{} -> {}'.format(l, r) for (l, r) in closedflows], sep='\n', end='\n\n')

    intoflows = {}
    
    for l, r, in closedflows:
        if isvar(r) and not isvar(l):
            append_elt(intoflows, getvar(r), l)
        

    solution = {}
    for k in intoflows:
        ksol, newfix = var_solution(k, intoflows)
        if ksol is not None:
            solution[k] = ksol
        elif newfix is not None:
            allfixes = fixed.copy()
            allfixes.update(newfix)
            debugprint ('RESTARTING')
            return solve(fixed=allfixes)

    return solution

# I(X)
def var_solution(x, intoflows):
    debugprint('Solving', x)
    intox = into(x, intoflows)
    if len(intox) == 0:
        return None, None

    join, intox = kind(intox[0], x), intox[1:]
    debugprint(join)
    for k in intox:
        debugprint(kind(k, x))
        join = lub(join, kind(k, x))

    sol = type_solution(join)
    
    if x in initial_bindings and not moreprec(initial_bindings[x], sol):
        debugprint ('Bad solution', sol, 'instead using', initial_bindings[x])
        return initial_bindings[x], None
    else:
        debugprint ('Solution', sol)
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
    elif isinstance(k1, retic_ast.Instance):
        if isinstance(k2, retic_ast.Instance) and k1.instanceof.subtype_of(k2.instanceof):
            return k1
        elif isinstance(k2, retic_ast.Instance) and k2.instanceof.subtype_of(k1.instanceof):
            return k2
        else:
            return retic_ast.Dyn()
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
        else: raise exc.UnimplementedException(t.froms, t.froms.__class__)
    elif isinstance(t, retic_ast.List):
        return retic_ast.List(retic_ast.FlowVariable(stripvar(t.elts), variables.ListEltVar(x)))
    elif isinstance(t, retic_ast.Instance):
        return t # ???
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
            return t.froms.types == [retic_ast.FlowVariable(stripvar(arg), variables.PosArgVar(x, n)) for \
                               n, arg in enumerate(t.froms.types)] and \
                t.to == retic_ast.FlowVariable(stripvar(t.to), variables.RetVar(x))
        else: raise exc.UnimplementedException(t.froms)
    elif isinstance(t, retic_ast.List):
        return t == retic_ast.List(retic_ast.FlowVariable(stripvar(t.elts), variables.ListEltVar(x)))
    elif isinstance(t, retic_ast.Instance):
        return True
    else: raise exc.UnimplementedException(t)

def dyncon(l, r):
    if isvar(l) or isvar(r):
        return False
    elif isinstance(l, retic_ast.Trusted):
        return dyncon(l.type, r)
    elif isinstance(r, retic_ast.Trusted):
        return dyncon(l, r.type)
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
    elif isinstance(l, retic_ast.Instance) and isinstance(r, retic_ast.Instance):
        return l.instanceof == r.instanceof
    else: return False

def make_variable(type):
    if isinstance(type, retic_ast.Trusted):
        type = type.type
    if isinstance(type, retic_ast.FlowVariable):
        return type

    var = variables.Root(next(varinsertion.gensym))
    initial_bindings[var] = type
    type = subflows(var, type)
    return retic_ast.FlowVariable(type, var)

def subflows(var, type):
    if isinstance(type, retic_ast.List):
        nvar = variables.ListEltVar(var)
        initial_bindings[nvar] = type.elts
        sf = subflows(nvar, type.elts)
        if isinstance(sf, retic_ast.FlowVariable):
            flowlog.append((sf.var, nvar))
            flowlog.append((nvar, sf.var))
            sf = sf.type
        return retic_ast.List(retic_ast.FlowVariable(sf, nvar))
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
    elif isinstance(new, retic_ast.Instance):
        return isinstance(orig, retic_ast.Instance) and new.instanceof.subtype_of(orig.instanceof)
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

def underlying(t):
    if isinstance(t, retic_ast.Trusted):
        return underlying(t.type)
    elif isinstance(t, retic_ast.FlowVariable):
        return underlying(t.type)
    else: return t

def revert_flows_on_fail(fn):
    def nfn(*args, **kwargs):
        global initial_bindings, flowlog, bottom
        if trackflows: 
            cbinds = initial_bindings.copy()
            cflows = flowlog[:]
            cbots = bottom[:]
            cmems = variables.members.copy()
        ret = fn(*args, **kwargs)
        if not ret and trackflows:
            initial_bindings = cbinds
            floglog = cflows
            bottom = cbots
            variables.members = cmems
        return ret
    return nfn
