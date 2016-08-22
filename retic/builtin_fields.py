from .retic_ast import *

s2s = Function(PosAT([]), Str())
s2b = Function(PosAT([]), Bool())


def basics(me):
    return {
        '__class__': Dyn(),
        '__delattr__': Function(PosAT([Str()]), Void()),
        '__dir__': Function(PosAT([]), Dict(Str(), Dyn())),
        '__doc__': Str(),
        '__eq__': Function(PosAT([me]), Bool()),
        '__format__': Function(ArbAT(), Str()),
        '__ge__': Function(PosAT([me]), Bool()),
        '__getattribute__': Function(ArbAT(), Dyn()),
        '__gt__': Function(PosAT([me]), Bool()),
        '__hash__': Function(PosAT([]), Int()),
        '__init__': Function(ArbAT(), Void()),
        '__le__': Function(PosAT([me]), Bool()),
        '__lt__': Function(PosAT([me]), Bool()),
        '__ne__': Function(PosAT([me]), Bool()),
        '__new__': Function(ArbAT(), me),
        '__reduce__': Function(ArbAT(), Dyn()),
        '__reduce_ex__': Function(ArbAT(), Dyn()),
        '__repr__': Function(PosAT([]), Str()),
        '__setattr__': Function(ArbAT(), Void()),
        '__sizeof__': Function(PosAT([]), Int()),
        '__str__': Function(PosAT([]), Str()),
        '__subclasshook__': Function(ArbAT(), Dyn())
    }

intfields = basics(Int())
intfields['to_bytes'] = Function(ArbAT(), Dyn())

def modfields(me):
    ret = basics(me)
    ret['__dict__'] = Dict(Str(), Dyn())
    return ret

def funcfields(me):
    ret = basics(me)
    ret['__annotations__'] = Dict(Str(), Dyn())
    ret['__call__'] = me
    ret['__closure__'] = Dyn()
    ret['__code__'] = Dyn()
    ret['__defaults__'] = Dyn()
    ret['__dict__'] = Dict(Str(), Dyn())
    ret['__get__'] = Function(ArbAT(), Function(ArbAT(), me.to))
    ret['__globals__'] = Dict(Str(), Dyn())
    ret['__kwdefaults__'] = Dyn()
    ret['__module__'] = Str()
    ret['__name__'] = Str()
    ret['__qualname__'] = Str()
    return ret

def dictfields(me):
    ret = basics(me)
    ret['__contains__'] = Function(PosAT([me.keys]), Bool())
    ret['__delitem__'] = Function(PosAT([me.keys]), Void())
    ret['__getitem__'] = Function(ArbAT, me.values)
    ret['__iter__'] = Dyn()
    ret['__setitem__'] = Function(PosAT([me.keys, me.values]), Void())
    ret['clear'] = Function(PosAT([]), Void())
    ret['copy'] = Function(PosAT([]), me)
    ret['fromkeys'] = Function(ArbAT(), Dyn())
    ret['get'] = Function(ArbAT(), me.values)
    ret['items'] = Function(PosAT([]), List(Tuple(me.keys, me.values)))
    ret['keys'] = Function(PosAT([]), List(me.keys))
    ret['pop'] = Function(PosAT([me.keys]), me.values)
    ret['popitem'] = Function(PosAT([]), Tuple(me.keys, me.values))
    ret['setdefault'] = Function(ArbAT(), Dyn())
    ret['update'] = Function(PosAT([me]), Void())
    ret['values'] = Function(PosAT([]), List(me.values))
    return ret


def setfields(me):
    ret = basics(me)
    ret['__and__'] = Function(PosAT([me]), me)
    ret['__contains__'] = Function(PosAT([me.elts]), Bool())
    ret['__iand__'] = Function(PosAT([me]), me)
    ret['__ior__'] = Function(PosAT([me]), me)
    ret['__isub__'] = Function(PosAT([me]), me)
    ret['__iter__'] = Dyn()
    ret['__ixor__'] = Function(PosAT([me]), me)
    ret['__len__'] = Function(PosAT([]), Int())
    ret['__or__'] = Function(PosAT([me]), me)
    ret['__ror__'] = Function(PosAT([me]), me)
    ret['__rand__'] = Function(PosAT([me]), me)
    ret['__rxor__'] = Function(PosAT([me]), me)
    ret['__rsub__'] = Function(PosAT([me]), me)
    ret['__sub__'] = Function(PosAT([me]), me)
    ret['add'] = Function(PosAT([me.elts]), Void())
    ret['clear'] = Function(PosAT([]), Void())
    ret['copy'] = Function(PosAT([]), me)
    ret['difference'] = Function(ArbAT(), me)
    ret['difference_update'] = Function(ArbAT(), Void())
    ret['discard'] = Function(PosAT([me.elts]), Void())
    ret['intersection'] = Function(ArbAT(), me)
    ret['intersection_update'] = Function(ArbAT(), Void())
    ret['isdisjoint'] = Function(PosAT([me]), Bool())
    ret['issubset'] = Function(PosAT([me]), Bool())
    ret['issuperset'] = Function(PosAT([me]), Bool())
    ret['pop'] = Function(PosAT([]), me.elts)
    ret['remove'] = Function(PosAT([me.elts]), Void())
    ret['symmetric_difference'] = Function(ArbAT(), me)
    ret['symmetric_difference_update'] = Function(ArbAT(), Void())
    ret['union'] = Function(ArbAT(), me)
    ret['update'] = Function(ArbAT(), Void())
    return ret
    

voidfields = basics(Void())
voidfields['__bool__'] = s2b

strfields = basics(Str())
strfields.update({
    'capitalize': s2s,
    'casefold': s2s,
    'center': Function(ArbAT(), Str()), # int x str?
    'count': Function(PosAT([Str()]), Int()),
    'encode': Function(ArbAT(), Str()), # str x str?
    'endswith': Function(ArbAT(), Bool()), # str x int?
    'expandtabs': Function(PosAT([Int()]), Str()),
    'find': Function(ArbAT(), Int()), # ??
    'format': Function(ArbAT(), Str()), # ??
    'format_map': Function(PosAT([Dyn()]), Str()),
    'index': Function(PosAT([Str()]), Int()),
    'isalnum': s2b,
    'isalpha': s2b,
    'isdecimal': s2b,
    'isdigit': s2b,
    'isidentifier': s2b,
    'islower': s2b,
    'isnumeric': s2b,
    'isprintable': s2b,
    'isspace': s2b,
    'istitle': s2b,
    'isupper': s2b,
    'join': Function(PosAT([HTuple(Str())]), Str()),
    'ljust': Function(ArbAT(), Str()), # int x str?
    'lower': s2s,
    'lstrip': Function(ArbAT(), Str()), # str?
    'maketrans': Function(ArbAT(), Dyn()), # ??
    'partition': Function(PosAT([Str()]), HTuple(Str())),
    'replace': Function(ArbAT(), Str()), # str * str * int?
    'rfind': Function(ArbAT(), Int()), # ??
    'rindex': Function(PosAT([Str()]), Int()),
    'rjust': Function(ArbAT(), Str()), # int x str?
    'rpartition': Function(PosAT([Str()]), HTuple(Str())),
    'rsplit': Function(ArbAT(), List(Str())), # str?
    'rstrip': Function(ArbAT(), Str()), # str?
    'split': Function(ArbAT(), List(Str())), # str?
    'splitlines': Function(ArbAT(), List(Str())), # int?
    'startswith': Function(ArbAT(), Bool()), # str x int?
    'strip': Function(ArbAT(), Str()), # str?
    'swapcase': s2s,
    'title': s2s,
    'upper': s2s,
    'zfill': Function(PosAT([Int()]), Str())
})
strfields['__add__'] = Function(PosAT([Str()]), Str())
strfields['__contains__'] = Function(PosAT([Str()]), Bool())
strfields['__getitem__'] = Function(ArbAT, Str())
strfields['__getnewargs__'] = Function(PosAT([]), Tuple(Str()))
strfields['__iter__'] = Dyn()
strfields['__mod__'] = Function(PosAT([Dyn()]), Str())
strfields['__mul__'] = Function(PosAT([Int()]), Str())
strfields['__rmod__'] = Function(PosAT([Dyn()]), Str())
strfields['__rmul__'] = Function(PosAT([Int()]), Str())
