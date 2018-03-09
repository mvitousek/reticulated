from .. import exc, retic_ast, argspec
from ..retic_ast import *
import inspect

class CType: 
    def __repr__(self):
        return self.__str__()
    def parts(self, ctbl):
        return []
    def vars(self, ctbl):
        return []
    def fields(self):
        return {}
    def subst(self, x, t):
        return self
    def bind(self):
        return self
    def __hash__(self):
        raise Exception
class CAT: 
    def __repr__(self):
        return self.__str__()
    def parts(self, ctbl):
        return []
    def vars(self, ctbl):
        return []
    def subst(self, x, t):
        return self
    def bind(self):
        return self
    def __eq__(self, other):
        raise Exception()
    def __hash__(self):
        raise Exception

class CPrimitive: 
    def __eq__(self, other):
        return type(self) == type(other)

class CDyn(CType): 
    def __str__(self):
        return "*"
    def __eq__(self, other):
        return isinstance(other, CDyn)
    def __hash__(self):
        return 1001


class CBot(CType): 
    def __str__(self):
        return "bot"#"⊥"
    def __eq__(self, other):
        return isinstance(other, CBot)
    def __hash__(self):
        return 1023

    

class CForAll(CType):
    def __init__(self, var, ty):
        self.var = var
        self.ty = ty
    def __str__(self):
        return "ALL {}.{}".format(self.var.name, self.ty)# "∀{}.{}".format(self.var.name, self.ty)
    def parts(self, ctbl):
        return self.ty.parts(ctbl)
    def vars(self, ctbl):
        return self.ty.vars(ctbl)
    def subst(self, x, t):
        if x is self.var:
            return self.ty.subst(x, t)
        else:
            return CForAll(self.var, self.ty.subst(x,t))
    def bind(self):
        return CForAll(self.var, self.ty.bind())
    def __eq__(self, other):
        return isinstance(other, CForAll) and self.var == other.var and self.ty == other.ty
    def __hash__(self):
        return (hash(self.var) + hash(self.ty)) * 103
    def instanciate(self):
        ret = self.ty.subst(self.var, CVar(self.var.name))
        if isinstance(ret, CForAll):
            return ret.instanciate()
        else: return ret


class CPolyVar(CType):
    def __init__(self, name):
        self.name = name
    def __str__(self):
        return '`' + self.name
    def subst(self, x, t):
        if x is self:
            return t
        else:
            return self
    def __eq__(self, other):
        return isinstance(other, CPolyVar) and self.name == other.name
    def __hash__(self):
        return hash(self.name) * 101

class CIntersection(CType):
    def __init__(self, types):
        self.types = types
    def __str__(self):
        return ' | '.join(str(s) for s in self.types)
    def parts(self, ctbl):
        return sum((t.parts(ctbl) for t in self.types), [])
    def vars(self, ctbl):
        return sum((t.vars(ctbl) for t in self.types), [])
    def subst(self, x, t):
        return CIntersection([ty.subst(x,t) for ty in self.types])
    def bind(self):
        return CIntersection([ty.bind() for ty in self.types])
    def __eq__(self, other):
        import itertools
        return isinstance(other, CIntersection) and all(st == ot for st, ot in itertools.zip_longest(self.types, other.types))
    def __hash__(self):
        return sum(hash(t) for t in self.types) * 137
    
class CTyVar(CType):
    def __init__(self, name):
        self.name = name
    def __str__(self):
        return '@' + self.name
    def subst(self, x, t):
        if x is self:
            return t
        else:
            return self
    def __eq__(self, other):
        return isinstance(other, CTyVar) and self.name == other.name
    def __hash__(self):
        return hash(self.name) * 19

class CBool(CType, CPrimitive): 
    def __str__(self):
        return "bool"
    def __hash__(self):
        return 1
class CStr(CType, CPrimitive): 
    def __str__(self):
        return "str"
    def __hash__(self):
        return 2
    def fields(self):
        sup = super().fields()
        sup.update({
            'join': CFunction(PosCAT([CList(CStr())]), CStr()),
            'format': CFunction(ReadOnlyArbCAT(), CStr()),
            'split': CFunction(ReadOnlyArbCAT(), CList(CStr())),
            'splitlines': CFunction(PosCAT([]), CList(CStr()))
        })
        return sup
class CInt(CType, CPrimitive): 
    def __str__(self):
        return "int"
    def __hash__(self):
        return 3
class CFloat(CType, CPrimitive): 
    def __str__(self):
        return "float"
    def __hash__(self):
        return 4
class CVoid(CType, CPrimitive): 
    def __str__(self):
        return "NoneType"
    def __hash__(self):
        return 5

class CSingletonInt(CType, CPrimitive): 
    def __init__(self, n:int):
        self.n = n
    def __str__(self):
        return "int({})".format(self.n)
    def __eq__(self, other):
        return isinstance(other, CSingletonInt) and self.n == other.n
    def __hash__(self):
        return self.n+7

class CList(CType): 
    def __init__(self, elts:CType):
        self.elts = elts
    def __str__(self):
        return "List[{}]".format(self.elts)
    def parts(self, ctbl):
        return [self.elts]
    def vars(self, ctbl):
        return self.elts.vars(ctbl)
    def fields(self):
        sup = super().fields()
        sup.update({
            'append': CFunction(PosCAT([self.elts]), CVoid()),
            'remove': CFunction(PosCAT([self.elts]), CVoid()),
            'insert': CFunction(PosCAT([CInt(), self.elts]), CVoid()),
            'pop': CFunction(PosCAT([]), self.elts)
        })
        return sup
    def subst(self, x, t):
        return CList(self.elts.subst(x,t))
    def __eq__(self, other):
        return isinstance(other, CList) and self.elts == other.elts
    def __hash__(self):
        return hash(self.elts) * 5

class CSet(CType): 
    def __init__(self, elts:CType):
        self.elts = elts
    def __str__(self):
        return "Set[{}]".format(self.elts)
    def parts(self, ctbl):
        return [self.elts]
    def fields(self):
        sup = super().fields()
        sup.update({
            'add': CFunction(PosCAT([self.elts]), CVoid()),
            'clear': CFunction(PosCAT([]), CVoid()),
            '__sub__': CFunction(PosCAT([self]), self),
            'copy': CFunction(PosCAT([]), self)
        })
        return sup
    def vars(self, ctbl):
        return self.elts.vars(ctbl)
    def subst(self, x, t):
        return CSet(self.elts.subst(x,t))
    def __eq__(self, other):
        return isinstance(other, CSet) and self.elts == other.elts
    def __hash__(self):
        return hash(self.elts) * 7

class CHTuple(CType): 
    def __init__(self, elts:CType):
        self.elts = elts
    def __str__(self):
        return "HTuple[{}]".format(self.elts)
    def parts(self, ctbl):
        return [self.elts]
    def vars(self, ctbl):
        return self.elts.vars(ctbl)
    def subst(self, x, t):
        return CHTuple(self.elts.subst(x,t))
    def __eq__(self, other):
        return isinstance(other, CHTuple) and self.elts == other.elts
    def __hash__(self):
        return hash(self.elts) * 11

class CTuple(CType): 
    def __init__(self, *elts):
        self.elts = elts
    def __str__(self):
        return "Tuple[{}]".format(self.elts)
    def parts(self, ctbl):
        return self.elts
    def vars(self, ctbl):
        return sum([v.vars(ctbl) for v in self.elts], [])
    def subst(self, x, t):
        return CTuple(*[v.subst(x,t) for v in self.elts])
    def __eq__(self, other):
        return isinstance(other, CTuple) and self.elts == other.elts
    def __hash__(self):
        return sum([hash(elt) for elt in self.elts], 6)

class CDict(CType): 
    def __init__(self, keys:CType, values:CType):
        self.keys = keys
        self.values = values
    def __str__(self):
        return "Dict[{},{}]".format(self.keys,self.values)
    def parts(self, ctbl):
        return [self.keys, self.values]
    def vars(self, ctbl):
        return self.keys.vars(ctbl) + self.values.vars(ctbl)
    def fields(self):
        sup = super().fields()
        sup.update({
            'values': CFunction(PosCAT([]), CSubscriptable(CVar('dvals'), self.values))
        })
        return sup
    def subst(self, x, t):
        return CDict(self.keys.subst(x,t), self.values.subst(x,t))
    def __eq__(self, other):
        return isinstance(other, CDict) and self.values == other.values and self.keys == other.keys
    def __hash__(self):
        return (hash(self.values) + hash(self.keys)) * 13


class CFunction(CType): 
    def __init__(self, froms:CAT, to:CAT):
        self.froms = froms
        self.to = to
    def __str__(self):
        return "{} -> {}".format(self.froms, self.to)
    def parts(self, ctbl):
        return [self.to] + self.froms.parts(ctbl)
    def vars(self, ctbl):
        return self.to.vars(ctbl) + self.froms.vars(ctbl)
    def subst(self, x, t):
        return CFunction(self.froms.subst(x,t), self.to.subst(x,t))
    def bind(self):
        return CFunction(self.froms.bind(), self.to)
    def __eq__(self, other):
        return isinstance(other, CFunction) and self.froms == other.froms and self.to == other.to
    def __hash__(self):
        return (hash(self.froms) + hash(self.to)) * 17

name_counter = 0
class CVar(CType):
    def __init__(self, name=None):
        global name_counter
        if name is None:
            name = '%anon'
        self.rootname = name
        self.name = '{}#{}'.format(name, name_counter)
        name_counter += 1
    def __str__(self):
        return self.name
    def vars(self, ctbl):
        return [self]
    def bind(self):
        return CVarBind(self)
    def subst(self, x, t):
        if x is self:
            return t
        else:
            return self
    def __eq__(self, other):
        return other is self
    def __hash__(self):
        return hash(self.name)

class CVarBind(CType):
    def __init__(self, var):
        assert isinstance(var, CVar) or isinstance(var, CVarBind)
        self.var = var
        self.rootname = self.var.rootname + '%bound'
    def __str__(self):
        return 'bind({})'.format(str(self.var))
    def subst(self, x, t):
        if x is self.var:
            return t.bind()
        else:
            return CVarBind(self.var.subst(x ,t))
    def vars(self, ctbl):
        return [self.var]
    def bind(self):
        return CVarBind(self)
    def __eq__(self, other):
        return isinstance(other, CVarBind) and other.var == self.var
    def __hash__(self):
        return hash(self.var) * 27
    

class CClass(CType):
    def __init__(self, name):
        self.name = name
    def __str__(self):
        return 'type({})'.format(self.name)
    def subst(self, x, t):
        return self
    def vars(self,ctbl):
        if self.name in ctbl:
            #We play this game to prevent cycles
            return ctbl[self.name].vars({c:ctbl[c] for c in ctbl if c != self.name})
        else: 
            return []
    def __eq__(self, other):
        return isinstance(other, CClass) and other.name == self.name
    def __hash__(self):
        return hash(self.name) * 31

class CInstance(CType):
    def __init__(self, instanceof):
        self.instanceof = instanceof
    def __str__(self):
        return self.instanceof
    def __eq__(self, other):
        return isinstance(other, CInstance) and other.instanceof == self.instanceof
    def subst(self, x, t):
        if self == x:
            return t
        else: return self
    def __hash__(self):
        return id(self) + hash(self.instanceof)
    def lookup(self, k, ctbl):
        return ctbl[self.instanceof].instance_lookup(k, ctbl)
    def vars(self,ctbl):
        if self.instanceof in ctbl:
            #We play this game to prevent cycles
            return ctbl[self.instanceof].vars({c:ctbl[c] for c in ctbl if c != self.instanceof})
        else:
            return []
    def types(self, ctbl):
        return ctbl[self.instanceof].types(ctbl)
    def __eq__(self, other):
        return isinstance(other, CInstance) and other.instanceof == self.instanceof
    def __hash__(self):
        return hash(self.instanceof) * 37

class CStructural(CType):
    def __init__(self, members):
        self.members = members
    def __str__(self):
        return str(self.members)
    def parts(self, ctbl):
        return list(self.members.values())
    def vars(self, ctbl):
        return sum([self.members[v].vars(ctbl) for v in self.members], [])
    def subst(self, x, t):
        return CStructural({mem: self.members[mem].subst(x,t) for mem in self.members})
    def lookup(self, k, ctbl):
        return self.members[k]
    def __eq__(self, other):
        return isinstance(other, CStructural) and all(mem in other.members for mem in self.members) and \
            all(mem in self.members for mem in other.members) and \
            all(other.members[mem] == self.members[mem] for mem in self.members)
    def __hash__(self):
        return sum([hash(mem) + hash(self.members[mem]) for mem in self.members], 0)
        
        
class CSubscriptable(CType): 
    def __init__(self, keys:CType, elts:CType):
        self.keys = keys
        self.elts = elts
    def __str__(self):
        return "Subscriptable[{},{}]".format(self.keys,self.elts)
    def parts(self, ctbl):
        return [self.keys, self.elts]
    def vars(self, ctbl):
        return self.keys.vars(ctbl) + self.elts.vars(ctbl)
    def subst(self, x, t):
        return CSubscriptable(self.keys.subst(x,t), self.elts.subst(x,t))
    def __eq__(self, other):
        return isinstance(other, CSubscriptable) and other.keys == self.keys and other.elts == self.elts
    def __hash__(self):
        return hash(self.keys) + hash(self.elts) * 37

class PosCAT(CAT):
    def __init__(self, types):
        self.types = types
    def __str__(self):
        return str(self.types)
    def parts(self, ctbl):
        return self.types
    def vars(self, ctbl):
        return sum([v.vars(ctbl) for v in self.types], [])
    def subst(self, x, t):
        return PosCAT([v.subst(x,t) for v in self.types])
    def bind(self):
        return PosCAT(self.types[1:])
    def __eq__(self, other):
        return isinstance(other, PosCAT) and len(self.types) == len(other.types) and \
            all(m1 == m2 for m1, m2 in zip(self.types, other.types))
    def __hash__(self):
        return sum([hash(mem) for mem in self.types], 0)

class ArbCAT(CAT): 
    def __str__(self):
        return "..."
    def __eq__(self, other):
        return isinstance(other, ArbCAT)
    def __hash__(self):
        return 10027


class ReadOnlyArbCAT(CAT): 
    def __str__(self):
        return "..."
    def __eq__(self, other):
        return isinstance(other, ReadOnlyArbCAT)
    def __hash__(self):
        return 10527

class SpecCAT(CAT):
    def __init__(self, spec):
        self.spec = spec
    def __str__(self)->str:
        return argspec.str(self.spec)
    def parts(self, ctbl):
        return [self.spec.parameters[p].annotation for p in self.spec.parameters]
    def vars(self, ctbl):
        return sum([v.vars(ctbl) for v in self.parts(ctbl)], [])
    def subst(self, x, t):
        ret = []
        for k in list(self.spec.parameters):
            v = self.spec.parameters[k]
            ret.append(v.replace(annotation=v.annotation.subst(x, t)))
        return SpecCAT(inspect.Signature(ret))
    def bind(self):
        ret = []
        for k in list(self.spec.parameters)[1:]:
            v = self.spec.parameters[k]
            ret.append(v)
        return SpecCAT(inspect.Signature(ret))
    def __eq__(self, other):
        return isinstance(other, SpecCAT) and self.spec == other.spec
    def __hash__(self):
        return sum([hash(self.spec.parameters[mem].name) for mem in self.spec.parameters], 0)

class VarCAT(CAT, CVar):
    def __init__(self, name):
        global name_counter
        if name is None:
            name = '%anonvars'
        self.rootname = name
        self.name = '{}#{}'.format(name, name_counter)
        name_counter += 1
    def __str__(self):
        return '[{}...]'.format(self.name)
    def subst(self, x, t):
        if x is self:
            return t
        else:
            return self

                
    
    
class NoMatch(Exception): pass

CONFIRM = 0
UNCONFIRM = 1
PENDING = 2
DENY = 3

def match(ctype, rtype, ctbl):
    if isinstance(ctype, CIntersection):
        for t in ctype.types:
            r, m = match(t, rtype, ctbl)
            if m != DENY:
                return r, m
        return ctype, DENY
    
    if isinstance(ctype, CForAll):
        ctype = ctype.instanciate()

    if isinstance(ctype, CVar):
        return ctype, PENDING
    if isinstance(ctype, CDyn):
        return ctype, UNCONFIRM
        
    # if isinstance(ctype, CSubscriptable) and isinstance(ctype.keys, CVar) and not isinstance(rtype, Subscbiptable):
    #     return PENDING
    if isinstance(ctype, CFunction) and isinstance(ctype.froms, VarCAT):
        return ctype, PENDING
    if isinstance(ctype, CClass) and isinstance(rtype, Function) and ctbl[ctype.name].supports('__init__', ctbl):
        init = ctbl[ctype.name].lookup('__init__', ctbl)
        return match(init.bind(), rtype, ctbl)
    if isinstance(ctype, CInstance) and isinstance(rtype, Function) and ctbl[ctype.instanceof].instance_supports('__call__', ctbl):
        init = ctbl[ctype.instanceof].instance_lookup('__call__', ctbl)
        return match(init, rtype, ctbl)

    if isinstance(ctype, CVarBind):
        return ctype, PENDING
        
    try: 
        r = ctype_match(ctype, rtype, ctbl)
        if r is None:
            raise Exception()
        return r, CONFIRM
    except NoMatch:
        return ctype, DENY
    

def ctype_match(ctype, rtype, ctbl):
    if isinstance(rtype, retic_ast.Dyn):
        return ctype
    elif isinstance(rtype, Int):
        if isinstance(ctype, CVar) or isinstance(ctype, CVarBind):
            return CInt()
        elif isinstance(ctype, CInt):
            return ctype
        elif isinstance(ctype, CSingletonInt):
            return ctype
        elif isinstance(ctype, CBool):
            return CBool()
        else:
            raise NoMatch(ctype, rtype)
    elif isinstance(rtype, SingletonInt):
        if isinstance(ctype, CVar) or isinstance(ctype, CVarBind):
            return CSingletonInt(rtype.n)
        elif isinstance(ctype, CSingletonInt) and ctype.n == rtype.n:
            return ctype
        else:
            raise NoMatch(ctype, rtype, rtype.n)
    elif isinstance(rtype, Bool):
        if isinstance(ctype, CVar) or isinstance(ctype, CVarBind):
            return CBool()
        elif isinstance(ctype, CBool):
            return ctype
        else:
            raise NoMatch(ctype, rtype)
    elif isinstance(rtype, Float):
        if isinstance(ctype, CVar) or isinstance(ctype, CVarBind):
            return CFloat()
        elif isinstance(ctype, CFloat):
            return ctype
        elif isinstance(ctype, CInt):
            return CFloat()
        elif isinstance(ctype, CSingletonInt):
            return CFloat()
        elif isinstance(ctype, CBool):
            return CFloat()
        else:
            raise NoMatch(ctype, rtype)
    elif isinstance(rtype, Void):
        if isinstance(ctype, CVar) or isinstance(ctype, CVarBind):
            return CVoid()
        elif isinstance(ctype, CVoid):
            return ctype
        else:
            raise NoMatch(ctype, rtype)
    elif isinstance(rtype, Str):
        if isinstance(ctype, CVar) or isinstance(ctype, CVarBind):
            return CStr()
        elif isinstance(ctype, CStr):
            return ctype
        else:
            raise NoMatch(ctype, rtype)
    elif isinstance(rtype, List):
        if isinstance(ctype, CVar) or isinstance(ctype, CVarBind):
            return CList(CVar(name=ctype.rootname + '%elt'))
        elif isinstance(ctype, CList):
            return ctype
        elif isinstance(ctype, CSubscriptable):
            return ctype
        elif isinstance(ctype, CHTuple):
            return CList(ctype.elts)
        else:
            raise NoMatch(ctype, rtype)
    elif isinstance(rtype, HTuple):
        if isinstance(ctype, CVar) or isinstance(ctype, CVarBind):
            return CHTuple(CVar(name=ctype.rootname + '%elt'))
        elif isinstance(ctype, CHTuple):
            return ctype
        elif isinstance(ctype, CList):
            return CHTuple(ctype.elts)
        else:
            raise NoMatch(ctype, rtype)
    elif isinstance(rtype, Set):
        if isinstance(ctype, CVar) or isinstance(ctype, CVarBind):
            return CSet(CVar(name=ctype.rootname + '%mem'))
        elif isinstance(ctype, CSet):
            return ctype
        else:
            raise NoMatch(ctype, rtype)
    elif isinstance(rtype, Dict):
        if isinstance(ctype, CVar) or isinstance(ctype, CVarBind):
            return CDict(CVar(name=ctype.rootname + '%keys'),CVar(name=ctype.rootname + '%vals'))
        elif isinstance(ctype, CDict):
            return ctype
        else:
            raise NoMatch(ctype, rtype)
    elif isinstance(rtype, Tuple):
        if isinstance(ctype, CVar) or isinstance(ctype, CVarBind):
            return CTuple(*[CVar(name=ctype.rootname + '%elt<{}>'.format(n)) for n in range(len(rtype.elts))])
        elif isinstance(ctype, CTuple) and len(ctype.elts) == len(rtype.elts):
            return ctype
        else:
            raise NoMatch(ctype, rtype)
    elif isinstance(rtype, Function):
        if isinstance(ctype, CVar) or isinstance(ctype, CVarBind):
            if isinstance(rtype.froms, PosAT):
                return CFunction(PosCAT([CVar(name=ctype.rootname + '%arg<{}>'.format(n)) for n in range(len(rtype.froms.types))]), CVar(name=ctype.rootname + '%return'))
            elif isinstance(rtype.froms, SpecAT):
                def to_speccat(spec):
                    nparams = []
                    for i, param in enumerate(spec.parameters):
                        nparams.append(spec.parameters[param].replace(annotation=CVar(name=ctype.rootname + '%arg<{}>'.format(i))))
                    return inspect.Signature(nparams)
                return CFunction(SpecCAT(to_speccat(rtype.froms.spec)), CVar(name=ctype.rootname + '%return'))
            elif isinstance(rtype.froms, ArbAT):
                return CFunction(ArbCAT(), CVar(name=ctype.rootname + '%return'))
                # We can get more precise info (probably) if we use VarCAT
               # return CFunction(VarCAT(name=ctype.rootname + '%args'), CVar(name=ctype.rootname + '%return'))
            else: raise NoMatch(ctype, rtype)
        elif isinstance(ctype, CIntersection):
            last_except = None
            for t in ctype.types:
                try:
                    return ctype_match(t, rtype, ctbl)
                except NoMatch as excep:
                    last_except = excep
            raise last_excep
        elif isinstance(ctype, CFunction):
            if isinstance(rtype.froms, PosAT):
                if isinstance(ctype.froms, PosCAT):
                    if len(ctype.froms.types) == len(rtype.froms.types):
                        return ctype
                    else: raise NoMatch(ctype, rtype)
                elif isinstance(ctype.froms, ArbCAT):
                    return ctype
                elif isinstance(ctype.froms, ReadOnlyArbCAT):
                    return ctype
                elif isinstance(ctype.froms, SpecCAT):
                    try:
                        ba = ctype.froms.spec.bind(*([None] * len(rtype.froms.types)))
                        return ctype
                    except TypeError:
                        raise NoMatch(ctype, rtype)
                else: raise NoMatch(ctype, rtype)
            elif isinstance(rtype.froms, ArbAT):
                return ctype
            elif isinstance(rtype.froms, SpecAT):
                if isinstance(ctype.froms, SpecCAT):
                    param_join = argspec.padjoin(ctype.froms.spec, rtype.froms.spec)
                    for ct, rt in param_join:
                        if ct:
                            if rt:
                                if not (ct.name == rt.name and ((ct.default and rt.default) or ct.default == rt.default)):
                                    raise NoMatch(ctype, rtype)
                            else:
                                if not ct.default:
                                    raise NoMatch(ctype, rtype)
                        else: raise NoMatch(ctype, rtype)
                    return ctype
                elif isinstance(ctype.froms, ArbCAT):
                    raise NoMatch(ctype, rtype)
                elif isinstance(ctype.froms, ReadOnlyArbCAT):
                    raise NoMatch(ctype, rtype)
                elif isinstance(ctype.froms, PosCAT):
                    raise NoMatch(ctype, rtype)
                else: raise NoMatch(ctype, rtype)
            else: raise NoMatch(ctype, rtype)
        elif isinstance(ctype, CClass) and ctbl[ctype.name].supports('__init__', ctbl):
            init = ctbl[ctype.name].lookup('__init__', ctbl)
            try:
                return ctype_match(init.bind(), rtype, ctbl)
            except NoMatch:
                raise NoMatch(ctype, rtype)
        elif isinstance(ctype, CInstance) and ctbl[ctype.instanceof].instance_supports('__call__', ctbl):
            init = ctbl[ctype.instanceof].instance_lookup('__call__', ctbl)
            try:
                return ctype_match(init, rtype, ctbl)
            except NoMatch:
                raise NoMatch(ctype, rtype)
        elif isinstance(ctype, CForAll):
            init = ctype.instanciate()
            try:
                return ctype_match(init, rtype, ctbl)
            except NoMatch:
                raise NoMatch(ctype, rtype)
        else:
            raise NoMatch(ctype, rtype)
    elif isinstance(rtype, Class):
        if isinstance(ctype, CVar) or isinstance(ctype, CVarBind):
            return CClass(rtype.name)
        elif isinstance(ctype, CClass) and ctype.name == rtype.name:
            return ctype
        else:
            raise NoMatch(ctype, rtype)
    elif isinstance(rtype, Instance):
        if isinstance(ctype, CVar) or isinstance(ctype, CVarBind):
            return CInstance(rtype.instanceof.name)
        elif isinstance(ctype, CInstance):
            if ctype.instanceof == rtype.instanceof.name:
                return ctype
            elif rtype.instanceof.name in ctbl[ctype.instanceof].superclasses(ctbl):
                return ctype
            else: raise NoMatch(ctype, rtype)
        elif isinstance(ctype, CVoid):
            return CInstance(rtype.instanceof.name)
        else:
            raise NoMatch(ctype, rtype)
    elif isinstance(rtype, Structural):
        if isinstance(ctype, CVar) or isinstance(ctype, CVarBind):
            return CStructural({k: CVar(name=ctype.rootname + '%attr<{}>'.format(k)) for k in rtype.members})
        elif isinstance(ctype, CStructural) and all(k in ctype.members for k in rtype.members):
            return ctype
        elif isinstance(ctype, CInstance):
            cls = ctbl[ctype.instanceof]
            if all(cls.instance_supports(k, ctbl) for k in rtype.members):
                #return ctype
                ret = CStructural({k: cls.instance_lookup(k, ctbl) for k in rtype.members})
                return ret
            else: raise NoMatch(ctype, rtype, cls, [(k, cls.instance_supports(k, ctbl)) for k in rtype.members])
        elif isinstance(ctype, CClass):
            cls = ctbl[ctype.name]
            if all(cls.supports(k, ctbl) for k in rtype.members):
                #return ctype
                ret = CStructural({k: cls.lookup(k, ctbl) for k in rtype.members})
                return ret
            else: raise NoMatch(ctype, rtype, cls, [(k, cls.supports(k, ctbl)) for k in rtype.members])
        elif all(k in ctype.fields() for k in rtype.members):
            return CStructural({k: ctype.fields()[k] for k in rtype.members})
        else:
            raise NoMatch(ctype, rtype)
    elif isinstance(rtype, Subscriptable):
        if isinstance(ctype, CVar) or isinstance(ctype, CVarBind):
            return CSubscriptable(CVar(name=ctype.rootname + '%key'), CVar(name=ctype.rootname + '%elt'))
        elif isinstance(ctype, CSubscriptable):
            return ctype
        elif isinstance(ctype, CList):
            return ctype
        elif isinstance(ctype, CDict):
            return ctype
        elif isinstance(ctype, CStr):
            return ctype
        elif isinstance(ctype, CTuple):
            return ctype
        elif isinstance(ctype, CHTuple):
            return ctype
        elif isinstance(ctype, CStructural) and '__getitem__' in ctype.members:
            return ctype
        else:
            raise NoMatch(ctype, rtype)
    else: raise NoMatch(ctype, type(rtype))
        
        
        
