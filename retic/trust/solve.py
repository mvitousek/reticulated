from .constraints import *
from .ctypes import *
from . import cgen_helpers
from .. import retic_ast, exc

class BailOut(Exception): pass

lower_bounds = {}
upper_bounds = {}
equals = {}
checked = {}
op_lower_bounds = {}
op_upper_bounds = {}
cls_lower_bounds = {}
elt_lower_bounds = {}
dep_on = {}
linked = set()
passed = set()

types = set()
typemap = {}
type_constraints = []
anormal_constraints = []
        

def dappend(dict, key, val):
    if key in dict:
        dict[key].add(val)
    else:
        dict[key] = {val}

LEFT = 0
RIGHT = 1
UN = 2

class Link:
    def __init__(self):
        self.upper_bounds = set()
        self.lower_bounds = set()
        self.op_upper_bounds = set()
        self.elt_upper_bounds = set()
        self.inst_upper_bounds = set()
        self.check_bounds = set()
        self.equal_bounds = set()
        self.subclass_bounds = set()
    def merge(self, other):
        self.upper_bounds |= other.upper_bounds
        self.lower_bounds |= other.lower_bounds
        self.op_upper_bounds |= other.op_upper_bounds
        self.elt_upper_bounds |= other.elt_upper_bounds
        self.inst_upper_bounds |= other.inst_upper_bounds
        self.check_bounds |= other.check_bounds
        self.equal_bounds |= other.equal_bounds
        self.subclass_bounds |= other.subclass_bounds
    def __repr__(self):
        s = ('\n>>Upper bounds: ' + str(self.upper_bounds))
        s += ('\n>>Lower bounds: ' + str(self.lower_bounds))
        s += ('\n>>Operator upper bounds: ' + str(self.op_upper_bounds))
        s += ('\n>>Element upper bounds: ' + str(self.elt_upper_bounds))
        s += ('\n>>Instance upper bounds: ' + str(self.inst_upper_bounds))
        s += ('\n>>Check bounds:' +  str(self.check_bounds))
        s += ('\n>>Equal bounds:' +  str(self.equal_bounds))
        s += ('\n>>Subclass bounds:' +  str(self.subclass_bounds) + '\n')
        return s

def setup_link(dct, k):
    if k not in dct:
        l = Link()
        dct[k] = l
        return l
    else:
        return dct[k]

def solve_vars(constraints, ctbl):
    links = {}
    initialize(links, constraints, ctbl)
    #print('\n\n\nVariable links:', links, '\n\n')
    solved = solve(links, ctbl)
    return list(reversed(solved))

def unsolvable(ctbl):
    return set(sum([c.r.vars(ctbl) for c in anormal_constraints if isinstance(c, CheckC)], []))
    
def unbinds_needed(l):
    if isinstance(l, CVar):
        return l, 0
    elif isinstance(l, CVarBind):
        v, n = unbinds_needed(l.var)
        return v, (n + 1)
    else: raise exc.InternalReticulatedError()

def iter_bind(l, n):
    if n == 0:
        return l
    else:
        return iter_bind(l.bind(), n - 1)

def iter_unbind(l, n):
    if n == 0:
        return l
    else:
        return iter_unbind(unbind(l), n - 1)


def initialize(links, constraints, ctbl):
    var_constraints = []
    type_constraints = []
    #print('Our Constraints', constraints)
    oc = None
    while oc != constraints:
        oc = constraints
        constraints = decompose(constraints, ctbl)
    #print('Simpl Constraints', constraints)


    for c in constraints:
        if isinstance(c, STC):
            if c.l != c.u:
                if isinstance(c.l, CVar) or isinstance(c.u, CVar) or isinstance(c.l, CVarBind) or isinstance(c.u, CVarBind):
                    if isinstance(c.l, CVar) or isinstance(c.l, CVarBind):
                        v, n = unbinds_needed(c.l)
                        link = setup_link(links, v)
                        link.upper_bounds.add((c.u, n))
                    if isinstance(c.u, CVar) or isinstance(c.u, CVarBind):
                        v, n = unbinds_needed(c.u)
                        link = setup_link(links, v)
                        link.lower_bounds.add((c.l, n))
                elif c.vars(ctbl):
                    var_constraints.append(c)
                else: 
                    type_constraints.append(c)
        elif isinstance(c, EqC):
            if c.l != c.r:
                if isinstance(c.l, CVar) or isinstance(c.r, CVar) or isinstance(c.l, CVarBind) or isinstance(c.r, CVarBind):
                    if isinstance(c.l, CVar) and isinstance(c.r, CVar):
                        linkl = setup_link(links, c.l)
                        linkr = setup_link(links, c.r)
                        linkl.merge(linkr)
                        links[c.r] = linkl

                    if isinstance(c.l, CVar) or isinstance(c.l, CVarBind):
                        v, n = unbinds_needed(c.l)
                        link = setup_link(links, v)
                        link.equal_bounds.add((c.r, n))
                    if isinstance(c.r, CVar) or isinstance(c.r, CVarBind):
                        v, n = unbinds_needed(c.r)
                        link = setup_link(links, v)
                        link.equal_bounds.add((c.l, n))
                elif c.vars(ctbl):
                    var_constraints.append(c)
                else: 
                    type_constraints.append(c)
        elif isinstance(c, CheckC):
            if c.l != c.r:
                if isinstance(c.l, CVar) or isinstance(c.l, CVarBind):
                    v, n = unbinds_needed(c.l)
                    link = setup_link(links, v)
                    link.check_bounds.add(((c.r, c.s), n))
                elif c.vars(ctbl):
                    var_constraints.append(c)
                else: 
                    type_constraints.append(c)
        elif isinstance(c, BinopSTC):
            varfound = False
            if isinstance(c.lo, CVar) or isinstance(c.lo, CVarBind):
                varfound = True
                v, n = unbinds_needed(c.lo)
                link = setup_link(links, v)
                link.op_upper_bounds.add(((LEFT, c), n))
            if isinstance(c.ro, CVar) or isinstance(c.ro, CVarBind):
                varfound = True
                v, n = unbinds_needed(c.ro)
                link = setup_link(links, v)
                link.op_upper_bounds.add(((RIGHT, c), n))
            if not varfound:
                raise exc.InternalReticulatedError()
        elif isinstance(c, UnopSTC):
            if isinstance(c.lo, CVar) or isinstance(c.lo, CVarBind):
                v, n = unbinds_needed(c.lo)
                link = setup_link(links, v)
                link.op_upper_bounds.add(((UN, c), n))
            else: 
                raise exc.InternalReticulatedError()
        elif isinstance(c, InheritsC):
            cls = ctbl[c.cls]
            for sup in c.supers:
                if isinstance(sup, CClass):
                    cls.inherits.append(sup.name)
                elif isinstance(sup, CDyn):
                    cls.dynamized = True
                elif isinstance(sup, CVar) or isinstance(sup, CVarBind):
                    v, n = unbinds_needed(sup)
                    link = setup_link(links, v)
                    link.subclass_bounds.add((c.cls, n))
                else:
                    raise Exception(c)
        elif isinstance(c, InstanceSTC):
            if isinstance(c.lc, CVar) or isinstance(c.lc, CVarBind):
                v, n = unbinds_needed(c.lc)
                link = setup_link(links, v)
                link.inst_upper_bounds.add((c.u, n))
            else:
                raise Exception(c)
        elif isinstance(c, EltSTC):
            if isinstance(c.lc, CVar) or isinstance(c.lc, CVarBind):
                v, n = unbinds_needed(c.lc)
                link = setup_link(links, v)
                link.elt_upper_bounds.add((c.u, n))
            else:
                raise Exception(c)
        else: raise Exception(c)

    

    nconstraints = []
    for var in links:
        equals = links[var].equal_bounds
        # vlb = lower_bounds.get(var, set())
        # vub = upper_bounds.get(var, set())
        # vc = checked.get(var, set())
        # voub = op_upper_bounds.get(var, set())
        for i, n in equals:
            for j, m in equals:
                if i is not j and (i, j) not in linked:
                    linked.add((i,j))
                    if n > m:
                        j = iter_bind(j, n-m)
                    else:
                        i = iter_bind(i, m-n)
                    nconstraints.append(EqC(i, j))
        #         ilb = lower_bounds.get(i, set())
        #         if vlb is not ilb:
        #             vlb |= ilb
        #             lower_bounds[i] = vlb
        #         iub = upper_bounds.get(i, set())
        #         if vub is not iub:
        #             vub |= iub
        #             upper_bounds[i] = vub
        #         ic = checked.get(i, set())
        #         if vc is not ic:
        #             vc |= ic
        #             checked[i] = vc
        #         ioub = op_upper_bounds.get(i, set())
        #         if voub is not ioub:
        #             voub |= ioub
        #             op_upper_bounds[i] = voub
        # wlb = lower_bounds.get(var, set())
        # if vlb is not wlb:
        #     lower_bounds[var] = vlb
        # wub = upper_bounds.get(var, set())
        # if vub is not wub:
        #     upper_bounds[var] = vub
        # wc = checked.get(var, set())
        # if vc is not wc:
        #     checked[var] = vc
        # woub = op_upper_bounds.get(var, set())
        # if voub is not woub:
        #     op_upper_bounds[var] = voub
        
                    
    def bind_as_needed(i, j, bindcount):
        if bindcount > 0:
            ip = i
            jp = iter_bind(j, bindcount)
        else:
            ip = iter_bind(i, -bindcount)
            jp = j
        return ip, jp
        
                    
    def lb_trans(bstring, cx):
        #print(links)
        nconstraints = []
        # for var in links:
        #     print (flush=True)
        #     print ('VAR:', var)
        #     print(links[var])
        #     print ('\tlb', all_bounds(var, 'lower_bounds', links))
        #     print ('\tub', all_bounds(var, 'upper_bounds', links))
        #     print ('\tolb', all_bounds(var, 'op_upper_bounds', links))
        #     print ('\tcb', all_bounds(var, 'check_bounds', links))
        #     print ('\teq', all_bounds(var, 'equal_bounds', links), flush=True)
        for var in links:
            int_passed = False
            int_dynamized = False
            for i, n in all_bounds(var, bstring, links):
                if isinstance(i, CVar) or isinstance(i, CVarBind):
                    continue
                if isinstance(i, CSingletonInt):
                    if not int_passed:
                        int_passed = True
                        last_int = i
                    elif not int_dynamized and int_passed and i != last_int:
                        int_dynamized = True
                        
                    if int_dynamized:
                        i = CInt()

                for j, m in all_bounds(var, 'upper_bounds', links):
                    if (i,j) not in linked:
                        linked.add((i,j))
                        bindcount = n - m
                        ip, jp = bind_as_needed(i, j, bindcount)
                        nconstraints.append(STC(ip, jp))
                if bstring != 'equal_bounds':
                    for j, m in all_bounds(var, 'equal_bounds', links): 
                        # if j is a var, then i should be in its bstring bounds
                        if (i,j) not in linked and not (isinstance(j, CVarBind) or isinstance(j, CVar)):
                            linked.add((i,j))
                            bindcount = n - m
                            ip, jp = bind_as_needed(i, j, bindcount)
                            nconstraints.append(cx(ip, jp))
                for (j, s), m in all_bounds(var, 'check_bounds', links):
                    # Case n=0, m=1:
                    # i should be bound
                    passed.add(var)
                    if (i,j) not in linked:
                        bindcount = n - m
                        ip, jp = bind_as_needed(i, j, bindcount)
                        while bindcount > 0:
                            #print(var, i, n, s, j, m)
                            s = s.bind(retic_ast.Dyn())
                            bindcount -= 1

                        matchres = match(ip, s, ctbl)
                        if matchres == CONFIRM:
                            linked.add((i,j))
                            nconstraints.append(cx(ip, jp))
                        elif matchres == DENY:
                            linked.add((i,j))
                            #print('Fail', var, i, j, ip, s, jp)
                            #print(bstring, '=lowbounds', all_bounds(var, 'lower_bounds', links), '\n', links[var].lower_bounds)
                            nconstraints.append(cx(ip, CDyn()))
                            nconstraints += [EqC(CDyn(), jpp) for jpp in jp.parts(ctbl)]
                for j, m in all_bounds(var, 'elt_upper_bounds', links):
                    if (i, j) not in linked:
                        linked.add((i,j))
                        bindcount = n - m
                        ip, jp = bind_as_needed(i, j, bindcount)
                        nconstraints.append(EltSTC(ip, jp))
                for j, m in all_bounds(var, 'inst_upper_bounds', links):
                    if (i, j) not in linked:
                        linked.add((i,j))
                        bindcount = n - m
                        ip, jp = bind_as_needed(i, j, bindcount)
                        nconstraints.append(InstanceSTC(ip, jp))
                for jcls, m in all_bounds(var, 'subclass_bounds', links):
                    if (i, jcls) not in linked:
                        linked.add((i,jcls))
                        bindcount = n - m
                        ip, _ = bind_as_needed(i, None, bindcount) # Inheriting from a bound thing doesn't seem to make sense
                        nconstraints.append(InheritsC([i], jcls))
                for (kind, c), m in all_bounds(var, 'op_upper_bounds', links):
                    if isinstance(c, UnopSTC):
                        if (i,c.u) not in linked:
                            linked.add((i,c.u))
                            nconstraints.append(UnopSTC(c.op, i, c.u))
                    elif isinstance(c, BinopSTC):
                        if kind == LEFT:
                            if isinstance(c.ro, CVar) or isinstance(c.ro, CVarBind):
                                ro, n = unbinds_needed(c.ro)
                                for j, k in all_bounds(ro, 'equal_bounds', links):
                                    if (i,j,c.u) not in linked:
                                        linked.add((i,j,c.u))
                                        nconstraints.append(BinopSTC(c.op, i, j, c.u))
                                for j, k in all_bounds(ro, 'lower_bounds', links):
                                    if (i,j,c.u) not in linked:
                                        linked.add((i,j,c.u))
                                        nconstraints.append(BinopSTC(c.op, i, j, c.u))
                            else:
                                if (i,c.u) not in linked:
                                    linked.add((i,c.u))
                                    nconstraints.append(BinopSTC(c.op, i, c.ro, c.u))
                        elif kind == RIGHT:
                            if isinstance(c.lo, CVar) or isinstance(c.lo, CVarBind):
                                lo, n = unbinds_needed(c.lo)
                                for j, k in all_bounds(lo, 'equal_bounds', links):
                                    if (j,i,c.u) not in linked:
                                        linked.add((j,i,c.u))
                                        nconstraints.append(BinopSTC(c.op, j, i, c.u))
                                for j, k in all_bounds(lo, 'lower_bounds', links):
                                    if (j,i,c.u) not in linked:
                                        linked.add((j,i,c.u))
                                        nconstraints.append(BinopSTC(c.op, j, i, c.u))
                            else:
                                if (i,c.u) not in linked:
                                    linked.add((i,c.u))
                                    nconstraints.append(BinopSTC(c.op, c.lo, i, c.u))
                # if var in equals:
                #     for j in equals[var]:
                #         if (i,j) not in linked:
                #             linked.add((i,j))
                #             nconstraints.append(EqC(i, j))
        # end lb_trans

        return nconstraints
    nconstraints += lb_trans('lower_bounds', STC)
    nconstraints += lb_trans('equal_bounds', EqC)
    # If we add another kind of bounds here we have to update the binop loops above

    
    if nconstraints or var_constraints:
        #print(len(nconstraints), sum([1 for n in nconstraints if isinstance(n, BinopSTC) or isinstance(n, UnopSTC)], 0) )#, 'new:', nconstraints)
        #print('pre-existing:', var_constraints)
        return initialize(links, list(set(var_constraints + nconstraints)), ctbl)

    #Is this safe?
    unsolved = set(sum([c.vars(ctbl) for c in nconstraints+var_constraints], []))
    #print(len(nconstraints))
    for var in links:
        if all(isinstance(v, CVar) or isinstance(v, CVarBind) for v in (all_bounds(var, 'equal_bounds', links) | all_bounds(var, 'lower_bounds', links))):
            #print('defaulting', var)
            nconstraints += [EqC(var, CBot())]
        # if var not in passed and var not in unsolved:
            # abs = all_bounds(var, 'check_bounds', links)
            # if abs:
            #     for (j, s), n in abs:
            #         passed.add(var)
            #         print('defaulting on', j, s, 'from', var)
            #         print([EqC(jp, CDyn()) for jp in j.parts(ctbl)] + ([EqC(j, CDyn())] if isinstance(j, CVar) else []))
            #         nconstraints += [EqC(jp, CDyn()) for jp in j.parts(ctbl)] + ([EqC(j, CDyn())] if isinstance(j, CVar) else []) 
            

    if nconstraints:
        #print(len(nconstraints), sum([1 for n in nconstraints if isinstance(n, BinopSTC) or isinstance(n, UnopSTC)], 0) )#, 'new:', nconstraints)
        #print('pre-existing:', var_constraints)
        return initialize(links, list(set(var_constraints + nconstraints)), ctbl)

                
def all_bounds(var, bound, links):
    vb = links[var]
    
    eqs = vb.equal_bounds
    if bound == 'equal_bounds':
        return eqs

    res = getattr(vb, bound)
    for evar, n in eqs: # Unbind from evar to var
        if isinstance(evar, CVar) or isinstance(evar, CVarBind):
            v, m = unbinds_needed(evar) # Number of times v is bo
            eb = links[v]
            if eb is vb:
                if m == n:
                    continue
                else:
                    raise Exception(var, vb, v, eb)

            ebbounds = getattr(eb, bound)
            for eres, k in ebbounds:
                bindcount = m - (n + k)
                if bindcount >= 0 and isinstance(eres, CType):
                    res.add((iter_bind(eres, bindcount), 0))
                else:
                    #print(var, '->', v, eres, m, n, k, ' = ', bindcount)
                    res.add((eres, -bindcount))
        # Case: n=0, m=1, k=0:
        # Result should be BOUND before adding to res
        # Case: n=1, m=0, k=0
        # Result should be UNBOUND before adding to res
    return res

def solve(links, ctbl):
    solved = []
    for var in links:
        vlb = all_bounds(var, 'lower_bounds', links)
        veq = all_bounds(var, 'equal_bounds', links)
        jtys = [v for v in (vlb | veq) if not isinstance(v[0], CVar) and not isinstance(v[0], CVarBind)]
        jty = join(jtys)
        all1 = [v for v in vlb]
        all2 = [v for v in veq]
        #print('solved', var, 'at', jty, 'with', jtys)
        solved.append(DefC(var, jty))
        [ctbl[cls].subst(var, jty) for cls in ctbl]
    #print(ctbl)
    return solved

def unbind(ty):
    if isinstance(ty, CFunction):
        if isinstance(ty.froms, PosCAT):
            return CFunction(PosCAT([CVar('dummy')] + ty.froms.types), ty.to)
        elif isinstance(ty.froms, SpecCAT):
            params = argspec.params(ty.froms.spec)
            if len(params) == 0:
                kind = inspect.Parameter.POSITIONAL_OR_KEYWORD
            elif params[0].kind == inspect.Parameter.POSITIONAL_ONLY:
                kind = inspect.Parameter.POSITIONAL_ONLY
            else:
                kind = inspect.Parameter.POSITIONAL_OR_KEYWORD
            return CFunction(SpecCAT(inspect.Signature([inspect.Parameter('dummy', kind, annotation=CVar('dummy'))] + params)), ty.to)
        elif isinstance(ty.froms, ArbCAT):
            return ty
        else:
            raise Exception()
    elif isinstance(ty, CVarBind):
        return ty.var
    elif isinstance(ty, CVar):
        raise Exception()
    else: 
        return ty

def join(tys):
    tys = [ty if not isinstance(ty, CForAll) else ty.instanciate() for ty in tys if not isinstance(ty, CBot)]
    if len(tys) == 0:
        return CDyn()
    join = tys[0][0]
    if tys[0][1]:
        join = unbind(join)
    for ty, bound in tys[1:]:
        if bound:
            ty = unbind(ty)

        

        if isinstance(join, CDyn):
            return join
        elif isinstance(join, CVar):
            raise Exception()
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
        elif isinstance(join, CFunction):
            if isinstance(ty, CFunction):
                if isinstance(join.froms, PosCAT):
                    if isinstance(ty.froms, PosCAT) and len(ty.froms.types) == len(join.froms.types):
                        join = CFunction(PosCAT([CVar('joinparam<{}>'.format(i)) for i in range(len(ty.froms.types))]),
                                         CVar('joinreturn'))
                    elif isinstance(ty.froms, PosCAT):
                        join = CFunction(ArbCAT(), CVar('joinreturn'))
                    elif isinstance(ty.froms, SpecCAT):
                        raise Exception()
                    else: raise Exception()
                elif isinstance(join.froms, SpecCAT):
                    if isinstance(ty.froms, SpecCAT):
                        argpairs = argspec.padjoin(join.froms.spec, ty.froms.spec)
                        ctor = lambda x: SpecCAT(inspect.Signature(x))
                        params = []
                        for i, (u, l) in enumerate(argpairs):
                            if u and l and u.name == l.name and ((u.default and l.default) or u.default == l.default):
                                params.append(inspect.Parameter(u.name, u.kind, default=u.default, annotation=CVar('joinparam<{}>'.format(i))))
                            elif u and l and argspec.order.index(u.kind) <= argspec.order.index(inspect.Parameter.POSITIONAL_OR_KEYWORD) and \
                                 u.default == inspect.Parameter.empty and u.default == l.default:
                                params = [p.annotation for p in params]
                                ctor = PosCAT
                                for j, (up, lp) in enumerate(argpairs[i:]):
                                    if up and lp and argspec.order.index(up.kind) <= argspec.order.index(inspect.Parameter.POSITIONAL_OR_KEYWORD) and \
                                       up.default == inspect.Parameter.empty and up.default == lp.default:
                                        params.append(CVar('joinparam<{}>'.format(i)))
                                    else:
                                        ctor = lambda x: ArbCAT()
                                        break
                                break
                            else:
                                ctor = lambda x: ArbCAT()
                                break
                        join = CFunction(ctor(params), CVar('joinreturn'))
                elif isinstance(join.froms, ArbCAT):
                    join = CFunction(ArbCAT(), CVar('joinreturn'))
                else: raise Exception()
            else: return CDyn()
        elif isinstance(join, CTuple):
            if isinstance(ty, CTuple) and len(ty.elts) == len(join.elts):
                join = CTuple(*[CVar('joinelt<{}>'.format(i)) for i in range(len(ty.elts))])
            else: return CDyn()
        elif isinstance(join, CHTuple):
            if isinstance(ty, CHTuple):
                join = CHTuple(CVar('joinelt'))
            else: return CDyn()
        elif isinstance(join, CList):
            if isinstance(ty, CList):
                join = CList(CVar('joinelt'))
            else: return CDyn()
        elif isinstance(join, CSet):
            if isinstance(ty, CSet):
                join = CSet(CVar('joinelt'))
            else: return CDyn()
        elif isinstance(join, CClass):
            if isinstance(ty, CClass) and join.name == ty.name:
                continue
            else: return CDyn()
        elif isinstance(join, CInstance):
            if isinstance(ty, CInstance) and join.instanceof == ty.instanceof:
                continue
            elif isinstance(ty, CVoid):
                continue
            else: return CDyn()
        elif isinstance(join, CStructural):
            if isinstance(ty, CStructural):
                join = CStructural({mem: CVar('joinmem<{}>'.format(mem)) for mem in join.members if mem in ty.members})
            else: return CDyn()
        elif isinstance(join, CSubscriptable):
            if isinstance(ty, CSubscriptable):
                join = CSubscriptable(CVar('joinkey'), CVar('joinelt'))
            else: return CDyn()
        elif isinstance(join, CStr):
            if isinstance(ty, CStr):
                continue
            else: return CDyn()
        elif isinstance(join, CVoid):
            if isinstance(ty, CInstance):
                join = ty
            elif isinstance(ty, CVoid):
                continue
            else: return CDyn()
        else: raise Exception(join, ty)
    return join

def transitive(constraints, ctbl, used):
    trans = []
    for i, c1 in enumerate(constraints):
        if isinstance(c1, STC) and isinstance(c1.u, CVar):
            clen = len(trans)
            for j, c2 in enumerate(constraints):
                if c1 is not c2:
                    if isinstance(c2, STC) and c2.l is c1.u and (c1.l,c2.l,c2.u) not in used:
                        trans.append(STC(c1.l, c2.u))
                        used.add((c1.l,c2.l,c2.u))
                    elif isinstance(c2, CheckC) and c2.l is c1.u:
                        if match(c1.l, c2.s, ctbl) == CONFIRM and (c1.l,c2.l,c2.r) not in used:
                            trans.append(STC(c1.l, c2.r))
                            used.add((c1.l,c2.l,c2.r))
                    elif isinstance(c2, EqC):
                        if c2.l is c1.u and (c1.l,c2.l,c2.r) not in used:
                            trans.append(STC(c1.l, c2.r))
                            used.add((c1.l,c2.l,c2.r))
                        if c2.r is c1.u and (c1.l, c2.r,c2.l) not in used:
                            trans.append(STC(c1.l, c2.l))
                            used.add((c1.l, c2.r,c2.l))
    return trans, used



def decompose_bivariant(constraints, c, l, r, ctbl, sym):
    if isinstance(l, CStructural) and not any(isinstance(r, ty) for ty in [CClass, CInstance, CStructural]):
        return decompose_bivariant(constraints, c, l, CStructural(r.fields()), ctbl, sym)
    if isinstance(r, CStructural) and not any(isinstance(l, ty) for ty in [CClass, CInstance, CStructural]):
        return decompose_bivariant(constraints, c, CStructural(l.fields()), r, ctbl, sym)

    ret = []
    assert not (isinstance(r, CVar) or isinstance(r, CDyn) or isinstance(r, CFunction)), (l, r)
    if isinstance(r, CList):
        if isinstance(l, CList):
            ret.append(EqC(l.elts, r.elts))
        elif isinstance(l, CSubscriptable):
            ret += [STC(CInt(), l.keys), EqC(l.elts, r.elts)]
        else: raise BailOut(l, sym, r)
    elif isinstance(r, CHTuple):
        if isinstance(l, CHTuple):
            ret.append(STC(l.elts, r.elts))
        elif isinstance(l, CSubscriptable):
            ret += [STC(CInt(), l.keys), EqC(l.elts, r.elts)]
        else: raise BailOut(l, sym, r)
    elif isinstance(r, CSet):
        if isinstance(l, CSet):
            ret.append(EqC(l.elts, r.elts))
        else: raise BailOut(l, sym, r)
    elif isinstance(r, CDict):
        if isinstance(l, CDict):
            ret.append(EqC(l.keys, r.keys))
            ret.append(EqC(l.values, r.values))
        elif isinstance(l, CSubscriptable):
            ret += [EqC(l.keys, r.keys), EqC(l.elts, r.keys)]
        else: raise BailOut(l, sym, r)
    elif isinstance(r, CTuple):
        if isinstance(l, CTuple) and len(l.elts) == len(r.elts):
            ret += [EqC(le, re) for le, re in zip(l.elts, r.elts)]
        elif isinstance(l, CSubscriptable):
            ret += [STC(CInt(), r.keys)] + [EqC(elt, l.elts) for elt in r.elts]
        else: raise BailOut(l, sym, r)
    elif isinstance(r, CInstance):
        if unsolvable_inherits(r, constraints):
            ret.append(c)
        elif isinstance(l, CVoid):
            pass
        elif isinstance(l, CInstance):
            if unsolvable_inherits(l, constraints):
                ret.append(c)
            elif r.instanceof in ctbl[l.instanceof].superclasses(ctbl):
                pass
            else:
                raise BailOut(l, sym, r)
        else: raise BailOut(l, sym, r)
    elif isinstance(r, CClass):
        if isinstance(l, CClass) and r.name == l.name:
            pass
        else: raise BailOut(l, sym, r)
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
        else: raise BailOut(l, sym, r)
    elif isinstance(r, CSubscriptable): # This may be able to be refined to subtyping in some cases if it goes back in decompose
        if isinstance(l, CSubscriptable):
            ret += [EqC(r.keys, l.keys), EqC(l.elts, r.elts)]
        elif isinstance(l, CList):
            ret += [STC(CInt(), r.keys), EqC(l.elts, r.elts)]
        elif isinstance(l, CStr):
            ret += [STC(CInt(), r.keys), STC(CStr(), r.elts)]
        elif isinstance(l, CHTuple):
            ret += [STC(CInt(), r.keys), EqC(l.elts, r.elts)]
        elif isinstance(l, CTuple): # With check constraints maybe we can do something here
            ret += [STC(CInt(), r.keys)] + [EqC(elt, r.elts) for elt in l.elts]
        elif isinstance(l, CDict):
            ret += [EqC(r.keys, l.keys), EqC(l.values, r.elts)]
        else: raise BailOut(l, sym, r, type(l), type(r))
    elif isinstance(r, CPrimitive):
        if isinstance(l, CPrimitive):
            pass
        elif isinstance(l, CInstance):
            pass
        else: raise BailOut(l, sym, r)
    elif isinstance(r, CVarBind):
        if isinstance(l, CVarBind):
            if r is l:
                pass
            else:
                ret += [EqC(l.var, r.var)]
        else: raise BailOut(l, sym, r)
    else: raise BailOut(l, sym, r)
    return ret

def unsolvable_inherits(ty, constraints):
    us = [c.cls for c in constraints if isinstance(c, InheritsC)]
    return (isinstance(ty, CClass) and ty.name in us) or (isinstance(ty, CInstance) and ty.instanceof in us) 

def decompose(constraints, ctbl):
    ret = []
    for c in constraints:
        if isinstance(c, InstanceSTC):
            if isinstance(c.lc, CVar):
                ret.append(c)
            elif isinstance(c.lc, CClass):
                ret.append(STC(CInstance(c.lc.name), c.u))
            elif isinstance(c.lc, CDyn):
                ret.append(STC(CDyn(), c.u))
            elif isinstance(c.lc, CBot):
                pass
            else:
                raise BailOut(c)
        elif isinstance(c, EltSTC):
            if isinstance(c.lc, CTuple):
                ret += [STC(l, c.u) for l in c.lc.elts]
            elif isinstance(c.lc, CList):
                ret.append(STC(c.lc.elts, c.u))
            elif isinstance(c.lc, CHTuple):
                ret.append(STC(c.lc.elts, c.u))
            elif isinstance(c.lc, CSubscriptable):
                ret.append(STC(c.lc.elts, c.u))
            elif isinstance(c.lc, CSet):
                ret.append(STC(c.lc.elts, c.u))
            elif isinstance(c.lc, CDict):
                ret.append(STC(c.lc.keys, c.u))
            elif isinstance(c.lc, CStr):
                ret.append(STC(CStr(), c.u))
            elif isinstance(c.lc, CDyn):
                ret.append(STC(CDyn(), c.u))
            elif isinstance(c.lc, CBot):
                pass
            elif isinstance(c.lc, CVar):
                ret.append(c)
            else:
                raise BailOut(c)
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
                    raise BailOut(c)
            if rsupers:
                ret.append(InheritsC(rsupers, c.cls))
        elif isinstance(c, BinopSTC):
            if not isinstance(c.lo, CVar) and not isinstance(c.ro, CVar) and \
               not isinstance(c.lo, CVarBind) and not isinstance(c.ro, CVarBind) and \
               not unsolvable_inherits(c.lo, constraints) and not unsolvable_inherits(c.ro, constraints):
                sol, sp = binop_solve(c.lo, c.op, c.ro, ctbl)
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
            if isinstance(c.l, CBot):
                pass
            elif isinstance(c.u, CVar):
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
                elif isinstance(c.l, CForAll):
                    ret.append(STC(c.l.instanciate(), CDyn()))
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
                    else: raise BailOut(c)
                elif isinstance(c.l, CList):
                    ret.append(EqC(c.l.elts, CDyn()))
                elif isinstance(c.l, CHTuple):
                    ret.append(STC(c.l.elts, CDyn()))
                elif isinstance(c.l, CSet):
                    ret.append(EqC(c.l.elts, CDyn()))
                elif isinstance(c.l, CDict):
                    ret += [EqC(c.l.keys, CDyn()), EqC(c.l.values, CDyn())]
                elif isinstance(c.l, CTuple):
                    ret += [STC(elt, CDyn()) for elt in c.l.elts]
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
                else: raise BailOut(c)
            elif isinstance(c.l, CDyn):
                ret += [STC(CDyn(), p) for p in c.l.parts(ctbl)]  
            elif isinstance(c.u, CHTuple):
                if isinstance(c.l, CHTuple):
                    ret.append(STC(c.l.elts, c.u.elts))
                elif isinstance(l, CSubscriptable):
                    ret += [STC(CInt(), c.l.keys), STC(c.l.elts, c.u.elts)]
                else: raise BailOut(c)
            elif isinstance(c.u, CTuple):
                if isinstance(c.l, CTuple) and len(c.l.elts) == len(c.u.elts):
                    ret += [STC(le, re) for le, re in zip(c.l.elts, c.u.elts)]
                elif isinstance(c.l, CSubscriptable):
                    ret += [STC(CInt(), c.u.keys)] + [STC(c.l.elts, elt) for elt in c.u.elts]
                else: raise BailOut(c)
            elif isinstance(c.u, CSubscriptable):
                if isinstance(c.l, CSubscriptable):
                    ret += [STC(c.l.keys, c.u.keys), EqC(c.l.elts, c.u.elts)]
                elif isinstance(c.l, CList):
                    ret += [STC(CInt(), c.u.keys), EqC(c.l.elts, c.u.elts)]
                elif isinstance(c.l, CSet):
                    ret += [STC(CInt(), c.u.keys), EqC(c.l.elts, c.u.elts)]
                elif isinstance(c.l, CStr):
                    ret += [STC(CInt(), c.u.keys), STC(CStr(), c.u.elts)]
                elif isinstance(c.l, CHTuple):
                    ret += [STC(CInt(), c.u.keys), STC(c.l.elts, c.u.elts)]
                elif isinstance(c.l, CTuple): # With check constraints maybe we can do something here
                    ret += [STC(CInt(), c.u.keys)] + [STC(elt, c.u.elts) for elt in c.l.elts]
                elif isinstance(c.l, CDict):
                    ret += [STC(c.l.keys, c.u.keys), EqC(c.l.values, c.u.elts)]
                else: raise BailOut(c)
            elif isinstance(c.u, CFunction):
                if isinstance(c.l, CFunction):
                    ret.append(STC(c.l.to, c.u.to))
                    if isinstance(c.l.froms, PosCAT):
                        if isinstance(c.u.froms, PosCAT) and len(c.l.froms.types) == len(c.u.froms.types):
                            ret += [STC(rp, lp) for lp, rp in zip(c.l.froms.types, c.u.froms.types)]
                        elif isinstance(c.u.froms, ArbCAT):
                            ret += [STC(CDyn(), lp) for lp in c.l.froms.types]
                        elif isinstance(c.u.froms, SpecCAT):
                            raise BailOut(c)
                        else: raise BailOut(c)
                    elif isinstance(c.l.froms, ArbCAT):
                        if isinstance(c.u.froms, PosCAT):
                            ret += [STC(rp, CDyn()) for rp in c.u.froms.types]
                        elif isinstance(c.u.froms, ArbCAT):
                            pass
                        elif isinstance(c.u.froms, SpecCAT):
                            params = argspec.params(c.u.froms.spec)
                            for u in params:
                                ret.append(STC(u.annotation, CDyn()))
                        else: raise BailOut(c)
                    elif isinstance(c.l.froms, SpecCAT):
                        if isinstance(c.u.froms, SpecCAT):
                            pairs = argspec.padjoin(c.u.froms.spec, c.l.froms.spec)
                            for u, l in pairs:
                                if u and l and u.name == l.name:
                                    ret.append(STC(u.annotation, l.annotation))
                                else: raise BailOut(c)
                        elif isinstance(c.u.froms, ArbCAT):
                            params = argspec.params(c.l.froms.spec)
                            for l in params:
                                ret.append(STC(CDyn(), l.annotation))
                        elif isinstance(c.u.froms, PosCAT):
                            #print('MATCH', c.l, c.u)
                            try:
                                ba = c.l.froms.spec.bind(*c.u.froms.types)
                            except TypeError:
                                raise BailOut(c)
                            for param in ba.arguments:
                                arg = ba.arguments[param]
                                _, paramty = argspec.paramty(param, c.l.froms.spec)
                                if isinstance(arg, dict):
                                    for key in arg:
                                        #print(paramty, arg[key])
                                        ret += [STC(arg[key], paramty)]
                                elif isinstance(arg, CType):
                                    #print(paramty, arg)
                                    ret += [STC(arg, paramty)]
                                elif isinstance(arg, tuple):
                                    for elt in arg:
                                        #print(paramty, elt)
                                        ret += [STC(elt, paramty)]
                                else: raise BailOut(c)
                        else: raise BailOut(c)
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
            elif isinstance(c.l, CDyn):
                ret += [EqC(CDyn(), p) for p in c.r.parts(ctbl)]
            elif isinstance(c.r, CFunction):
                if isinstance(c.l, CForAll):
                    c.l = c.l.instanciate()

                if isinstance(c.l, CFunction):
                    ret.append(EqC(c.l.to, c.r.to))
                    if isinstance(c.l.froms, PosCAT):
                        if isinstance(c.r.froms, PosCAT) and len(c.l.froms.types) == len(c.r.froms.types):
                            ret += [EqC(rp, lp) for lp, rp in zip(c.l.froms.types, c.r.froms.types)]
                        elif isinstance(c.r.froms, ArbCAT):
                            ret += [EqC(CDyn(), lp) for lp in c.l.froms.types]
                        # elif isinstance(c.r.froms, VarCAT):
                        #     ret.append(EqC(c.l.froms, c.r.froms))
                        else: raise BailOut(c)
                    elif isinstance(c.l.froms, ArbCAT):
                        if isinstance(c.r.froms, PosCAT):
                            ret += [EqC(rp, CDyn()) for rp in c.r.froms.types]
                        elif isinstance(c.r.froms, ArbCAT):
                            pass
                        else: raise BailOut(c)
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
                                    else: raise BailOut(c)
                            except TypeError:
                                raise BailOut(c)
                        else: raise BailOut(c)
                    # elif isinstance(c.l.froms, VarCAT):
                    #     if isinstance(c.r.froms, VarCAT):
                    #         ret.append(EqC(c.l.froms, c.r.froms))
                    #     else:
                    #         raise BailOut(c)
                    else: raise BailOut(c)
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
                    else: raise BailOut(c)
                elif isinstance(c.l, CClass):
                    if unsolvable_inherits(c.l, constraints):
                        ret.append(c)
                        continue
                    if ctbl[c.l.name].supports('__init__', ctbl):
                        init = CFunction(ctbl[c.l.name].lookup('__init__', ctbl).bind().froms, CInstance(c.l.name))
                        ret.append(EqC(init, c.r))
                    else: raise BailOut(c)
                else: raise BailOut(c)
            else: ret += decompose_bivariant(constraints, c, c.l, c.r, ctbl, '=')
        elif isinstance(c, CheckC):
            if unsolvable_inherits(c.l, constraints):
                ret.append(c)
                continue

            
            if isinstance(c.l, CClass) and isinstance(c.s, Function) and ctbl[c.l.name].supports('__init__', ctbl):
                init = ctbl[c.l.name].lookup('__init__', ctbl)
                #print('switch', c.l, init.bind(), c.s)
                ret.append(CheckC(init.bind(), c.s, c.r))
                continue
            if isinstance(c.l, CInstance) and isinstance(c.s, Function) and ctbl[c.l.instanceof].instance_supports('__call__', ctbl):
                init = ctbl[c.l.instanceof].instance_lookup('__call__', ctbl)
                #print('switch', c.l, init.bind(), c.s)
                ret.append(CheckC(init, c.s, c.r))
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
#        print('binop', fn, *args, '=', ret)
        if not isinstance(ret, tuple):
            return ret, []
        else: return ret
    return inner

@prop_constraints
def binop_solve(l, op, r, ctbl):
    from ..consistency import getop, getopmeth

    def apply_binop_method(l, r):
        ldummy = ast.Name(id='ldummy', ctx=ast.Load(), lineno=0, col_offset=0)
        ldummy.retic_ctype = l
        rdummy = ast.Name(id='rdummy', ctx=ast.Load(), lineno=0, col_offset=0)
        rdummy.retic_ctype = r
        lmeth, rmeth = getopmeth(op)
        if isinstance(l, CStructural) and lmeth in l.members:
            lfunc = l.members[lmeth]
            if isinstance(lfunc, CVar) or isinstance(lfunc, CVarBind):
                rtype = retic_ast.Function(retic_ast.PosAT([retic_ast.Dyn()]), retic_ast.Dyn())
                match = ctype_match(lfunc, rtype, ctbl)
                st = [CheckC(lfunc, rtype, match)]
                lfunc = match
            else:
                st = []
            r, stp = cgen_helpers.apply(ldummy, lfunc, [rdummy], [], None, None, ctbl)
            return r, list(stp) + st
        elif isinstance(l, CInstance) and ctbl[l.instanceof].instance_supports(lmeth, ctbl):
            lfunc = ctbl[l.instanceof].instance_lookup(lmeth, ctbl) 
            if isinstance(lfunc, CVar) or isinstance(lfunc, CVarBind):
                rtype = retic_ast.Function(retic_ast.PosAT([retic_ast.Dyn()]), retic_ast.Dyn())
                match = ctype_match(lfunc, rtype, ctbl)
                st = [CheckC(lfunc, rtype, match)]
                lfunc = match
            else:
                st = []
            r, stp = cgen_helpers.apply(ldummy, lfunc, [rdummy], [], None, None, ctbl)
            return r, list(stp) + st
        elif isinstance(r, CStructural) and rmeth in r.members:
            rfunc = r.members[rmeth]
            if isinstance(lfunc, CVar) or isinstance(lfunc, CVarBind):
                rtype = retic_ast.Function(retic_ast.PosAT([retic_ast.Dyn()]), retic_ast.Dyn())
                match = ctype_match(rfunc, rtype, ctbl)
                st = [CheckC(rfunc, rtype, match)]
                rfunc = match
            else:
                st = []
            r, stp = cgen_helpers.apply(rdummy, rfunc, [ldummy], [], None, None, ctbl)
            return r, list(stp) + st
        elif isinstance(r, CInstance) and ctbl[r.instanceof].instance_supports(rmeth, ctbl):
            rfunc = ctbl[r.instanceof].instance_lookup(rmeth, ctbl) 
            if isinstance(lfunc, CVar) or isinstance(lfunc, CVarBind):
                rtype = retic_ast.Function(retic_ast.PosAT([retic_ast.Dyn()]), retic_ast.Dyn())
                match = ctype_match(rfunc, rtype, ctbl)
                st = [CheckC(rfunc, rtype, match)]
                rfunc = match
            else:
                st = []
            r, stp = cgen_helpers.apply(rdummy, rfunc, [ldummy], [], None, None, ctbl)
            return r, list(stp) + st
        else:
            return CDyn()
                
    if isinstance(l, CDyn):
        return CDyn()
    elif (not isinstance(op, ast.Mod) or not isinstance(l, CStr))\
         and isinstance(r, CDyn): # If LHS is a string and op is %, then we def have a string
        return CDyn()
        

    elif isinstance(op, ast.Add):
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
            return apply_binop_method(l, r)
    elif isinstance(op, ast.Sub) or isinstance(op, ast.Pow): # These ones can take floats
        if isinstance(l, CSingletonInt) and isinstance(r, CSingletonInt):
            return CSingletonInt(getop(op)(l.n, r.n))
        elif intlike(l) and intlike(r):
            return CInt()
        elif floatlike(l) and floatlike(r):
            return CFloat()
        else: 
            return apply_binop_method(l, r)
    elif isinstance(op, ast.Div):
        if floatlike(l) and floatlike(r):
            return CFloat()
        else: 
            return apply_binop_method(l, r)
    elif isinstance(op, ast.FloorDiv): # Takes floats, but always return int
        if isinstance(l, CSingletonInt) and isinstance(r, CSingletonInt):
            return CSingletonInt(getop(op)(l.n, r.n))
        elif floatlike(l) and floatlike(r):
            return CInt()
        else: 
            return apply_binop_method(l, r)
    elif isinstance(op, ast.LShift) or isinstance(op, ast.RShift) or \
         isinstance(op, ast.BitOr) or isinstance(op, ast.BitXor) or isinstance(op, ast.BitAnd): # These ones cant
        if isinstance(l, CSingletonInt) and isinstance(r, CSingletonInt):
            return CSingletonInt(getop(op)(l.n, r.n))
        elif intlike(l) and intlike(r):
            return CInt()
        else: 
            return apply_binop_method(l, r)
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
            return apply_binop_method(l, r)
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
            return apply_binop_method(l, r)
    else:
        raise exc.InternalReticulatedError(op)

    
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
            return CDyn()
    elif isinstance(op, ast.UAdd) or isinstance(op, ast.USub):
        if isinstance(o, CSingletonInt):
            return CSingletonInt(o.n if isinstance(op, ast.UAdd) else -o.n)
        elif intlike(o): #yes float
            return CInt()
        elif floatlike(o): 
            return CFloat()
        else:
            return CDyn()

