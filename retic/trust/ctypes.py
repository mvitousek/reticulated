from .. import exc, retic_ast
from ..retic_ast import *

class CType: 
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

class CPrimitive: pass

class CDyn(CType): 
    def __str__(self):
        return "*"

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

class CBool(CType, CPrimitive): 
    def __str__(self):
        return "bool"
class CStr(CType, CPrimitive): 
    def __str__(self):
        return "str"
class CInt(CType, CPrimitive): 
    def __str__(self):
        return "int"
class CFloat(CType, CPrimitive): 
    def __str__(self):
        return "float"
class CVoid(CType, CPrimitive): 
    def __str__(self):
        return "NoneType"

class CSingletonInt(CType, CPrimitive): 
    def __init__(self, n:int):
        self.n = n
    def __str__(self):
        return "int({})".format(self.n)

class CList(CType): 
    def __init__(self, elts:CType):
        self.elts = elts
    def __str__(self):
        return "List[{}]".format(self.elts)
    def parts(self, ctbl):
        return [self.elts]
    def vars(self, ctbl):
        return self.elts.vars(ctbl)
    def subst(self, x, t):
        return CList(self.elts.subst(x,t))

class CSet(CType): 
    def __init__(self, elts:CType):
        self.elts = elts
    def __str__(self):
        return "Set[{}]".format(self.elts)
    def parts(self, ctbl):
        return [self.elts]
    def vars(self, ctbl):
        return self.elts.vars(ctbl)
    def subst(self, x, t):
        return CSet(self.elts.subst(x,t))

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
    def subst(self, x, t):
        return CDict(self.keys.subst(x,t), self.values.subst(x,t))


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
    def subst(self, x, t):
        if x is self:
            return t
        else:
            return self

class CClass(CType):
    def __init__(self, name):
        self.name = name
    def __str__(self):
        return 'type({})'.format(self.name)
    def subst(self, x, t):
        return self
    def vars(self,ctbl):
        return ctbl[self.name].vars(ctbl)

class CInstance(CType):
    def __init__(self, instanceof):
        self.instanceof = instanceof
    def __str__(self):
        return self.instanceof
    def subst(self, x, t):
        return self
    def lookup(self, k, ctbl):
        return ctbl[self.instanceof].instance_lookup(k, ctbl)
    def vars(self,ctbl):
        return ctbl[self.instanceof].vars(ctbl)
    def types(self, ctbl):
        return ctbl[self.instanceof].types(ctbl)

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

class ArbCAT(CAT): 
    def __str__(self):
        return "{*}"

class NoMatch(Exception): pass

CONFIRM = 0
UNCONFIRM = 1
PENDING = 2
DENY = 3

def match(ctype, rtype, ctbl):
    if isinstance(rtype, retic_ast.Dyn):
        return CONFIRM
    if isinstance(ctype, CVar):
        return PENDING
    if isinstance(ctype, CDyn):
        return UNCONFIRM


    # try: 
    #     ctype_match(ctype, rtype, ctbl)
    #     return CONFIRM
    # except NoMatch:
    #     return DENY

    if isinstance(rtype, Int):
        if isinstance(ctype, CInt):
            return CONFIRM
        elif isinstance(ctype, CSingletonInt):
            return CONFIRM
        elif isinstance(ctype, CBool):
            return CONFIRM
        else:
            return DENY
    elif isinstance(rtype, SingletonInt):
        if isinstance(ctype, CSingletonInt) and ctype.n == rtype.n:
            return CONFIRM
        else:
            raise DENY
    elif isinstance(rtype, Bool):
        if isinstance(ctype, CBool):
            return CONFIRM
        else:
            return DENY
    elif isinstance(rtype, SingletonInt):
        if isinstance(ctype, CSingletonInt) and ctype.n == rtype.n:
            return CONFIRM
        else:
            return DENY
    elif isinstance(rtype, Float):
        if isinstance(ctype, CFloat):
            return CONFIRM
        elif isinstance(ctype, CInt):
            return CONFIRM
        elif isinstance(ctype, CSingletonInt):
            return CONFIRM
        elif isinstance(ctype, CBool):
            return CONFIRM
        else:
            return DENY
    elif isinstance(rtype, Str):
        if isinstance(ctype, CStr):
            return CONFIRM
        else:
            return DENY
    elif isinstance(rtype, List):
        if isinstance(ctype, CList):
            return CONFIRM
        elif isinstance(ctype, CHTuple):
            return CONFIRM
        else:
            return DENY
    elif isinstance(rtype, HTuple):
        if isinstance(ctype, CHTuple):
            return CONFIRM
        elif isinstance(ctype, CList):
            return CONFIRM
        else:
            return DENY
    elif isinstance(rtype, Set):
        if isinstance(ctype, CSet):
            return CONFIRM
        else:
            return DENY
    elif isinstance(rtype, Dict):
        if isinstance(ctype, CDict):
            return CONFIRM
        else:
            return DENY
    elif isinstance(rtype, Tuple):
        if isinstance(ctype, CTuple) and len(ctype.elts) == len(rtype.elts):
            return CONFIRM
        else:
            return DENY
    elif isinstance(rtype, Function):
        if isinstance(ctype, CFunction) and len(ctype.froms.types) == len(rtype.froms.types):
            return CONFIRM
        elif isinstance(ctype, CClass) and ctbl[ctype.name].supports('__init__', ctbl):
            init = ctbl[ctype.name].lookup('__init__', ctbl)
            if isinstance(init, CFunction) and len(init.froms.types) - 1 == len(rtype.froms.types):
                return CONFIRM
            else:
                return DENY
        else:
            return DENY
    elif isinstance(rtype, Class):
        if isinstance(ctype, CClass) and ctype.name == rtype.name:
            return CONFIRM
        else: return DENY
    elif isinstance(rtype, Instance):
        if isinstance(ctype, CInstance):
            if ctype.instanceof == rtype.instanceof.name:
                return CONFIRM
            elif rtype.instanceof.name in ctbl[ctype.instanceof].superclasses(ctbl):
                return CONFIRM
            else: DENY
        else: return DENY
    elif isinstance(rtype, Structural):
        if isinstance(ctype, CStructural) and all(k in ctype.members for k in rtype.members):
            return CONFIRM
        elif isinstance(ctype, CInstance):
            cls = ctbl[ctype.instanceof]
            if all(cls.instance_supports(k, ctbl) for k in rtype.members):
                return CONFIRM
            else: return DENY
        else:
            return DENY
    elif isinstance(rtype, Subscriptable):
        if isinstance(ctype, CSubscriptable):
            return CONFIRM
        elif isinstance(ctype, CList):
            return CONFIRM
        elif isinstance(ctype, CDict):
            return CONFIRM
        elif isinstance(ctype, CStr):
            return CONFIRM
        elif isinstance(ctype, CTuple):
            return CONFIRM
        elif isinstance(ctype, CHTuple):
            return CONFIRM
        elif isinstance(ctype, CStructural) and '__getitem__' in ctype.members:
            return CONFIRM
        else:
            return DENY

def ctype_match(ctype, rtype, ctbl):
    if isinstance(rtype, retic_ast.Dyn):
        return ctype
    elif isinstance(rtype, Int):
        if isinstance(ctype, CVar):
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
        if isinstance(ctype, CVar):
            return CSingletonInt(rtype.n)
        elif isinstance(ctype, CSingletonInt) and ctype.n == rtype.n:
            return ctype
        else:
            raise NoMatch(ctype, rtype, rtype.n)
    elif isinstance(rtype, Bool):
        if isinstance(ctype, CVar):
            return CBool()
        elif isinstance(ctype, CBool):
            return ctype
        else:
            raise NoMatch(ctype, rtype)
    elif isinstance(rtype, Float):
        if isinstance(ctype, CVar):
            return CFloat()
        elif isinstance(ctype, CFloat):
            return ctype
        elif isinstance(ctype, CInt):
            return CFloat()
        elif isinstance(ctype, CBool):
            return CFloat()
        else:
            raise NoMatch(ctype, rtype)
    elif isinstance(rtype, Str):
        if isinstance(ctype, CVar):
            return CStr()
        elif isinstance(ctype, CStr):
            return ctype
        else:
            raise NoMatch(ctype, rtype)
    elif isinstance(rtype, List):
        if isinstance(ctype, CVar):
            return CList(CVar(name=ctype.rootname + '%elt'))
        elif isinstance(ctype, CList):
            return ctype
        elif isinstance(ctype, CHTuple):
            return CList(ctype.elts)
        else:
            raise NoMatch(ctype, rtype)
    elif isinstance(rtype, HTuple):
        if isinstance(ctype, CVar):
            return CHTuple(CVar(name=ctype.rootname + '%elt'))
        elif isinstance(ctype, CHTuple):
            return ctype
        elif isinstance(ctype, CList):
            return CHTuple(ctype.elts)
        else:
            raise NoMatch(ctype, rtype)
    elif isinstance(rtype, Set):
        if isinstance(ctype, CVar):
            return CSet(CVar(name=ctype.rootname + '%mem'))
        elif isinstance(ctype, CSet):
            return ctype
        else:
            raise NoMatch(ctype, rtype)
    elif isinstance(rtype, Dict):
        if isinstance(ctype, CVar):
            return CDict(CVar(name=ctype.rootname + '%keys'),CVar(name=ctype.rootname + '%vals'))
        elif isinstance(ctype, CDict):
            return ctype
        else:
            raise NoMatch(ctype, rtype)
    elif isinstance(rtype, Tuple):
        if isinstance(ctype, CVar):
            return CTuple(*[CVar(name=ctype.rootname + '%elt<{}>'.format(n)) for n in range(len(rtype.elts))])
        elif isinstance(ctype, CTuple) and len(ctype.elts) == len(rtype.elts):
            return ctype
        else:
            raise NoMatch(ctype, rtype)
    elif isinstance(rtype, Function):
        if isinstance(ctype, CVar):
            return CFunction(PosCAT([CVar(name=ctype.rootname + '%arg<{}>'.format(n)) for n in range(len(rtype.froms.types))]), CVar(name=ctype.rootname + '%return'))
        elif isinstance(ctype, CFunction) and len(ctype.froms.types) == len(rtype.froms.types):
            return ctype
        elif isinstance(ctype, CClass) and ctbl[ctype.name].supports('__init__', ctbl):
            init = ctbl[ctype.name].lookup('__init__', ctbl)
            if isinstance(init, CFunction) and len(init.froms.types) - 1 == len(rtype.froms.types):
                return ctype
            else:
                raise NoMatch(ctype, rtype)
        else:
            raise NoMatch(ctype, rtype)
    elif isinstance(rtype, Class):
        if isinstance(ctype, CVar):
            return CClass(rtype.name)
        elif isinstance(ctype, CClass) and ctype.name == rtype.name:
            return ctype
        else:
            raise NoMatch(ctype, rtype)
    elif isinstance(rtype, Instance):
        if isinstance(ctype, CVar):
            return CInstance(rtype.instanceof.name)
        elif isinstance(ctype, CInstance):
            if ctype.instanceof == rtype.instanceof.name:
                return ctype
            elif rtype.instanceof.name in ctbl[ctype.instanceof].superclasses(ctbl):
                return ctype
            else: raise NoMatch(ctype, rtype)
        else:
            raise NoMatch(ctype, rtype)
    elif isinstance(rtype, Structural):
        if isinstance(ctype, CVar):
            return CStructural({k: CVar(name=ctype.rootname + '%attr<{}>'.format(k)) for k in rtype.members})
        elif isinstance(ctype, CStructural) and all(k in ctype.members for k in rtype.members):
            return ctype
        elif isinstance(ctype, CInstance):
            cls = ctbl[ctype.instanceof]
            if all(cls.instance_supports(k, ctbl) for k in rtype.members):
                return ctype
            else: raise NoMatch(ctype, rtype)
        else:
            raise NoMatch(ctype, rtype)
    elif isinstance(rtype, Subscriptable):
        if isinstance(ctype, CVar):
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
        
        
        
