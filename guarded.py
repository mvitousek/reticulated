import typing, inspect, rtypes
from typing import tyinstance as retic_tyinstance, has_type as retic_has_type, subcompat as retic_subcompat,\
    has_shape as retic_has_shape, pinstance as retic_pinstance
from relations import merge as retic_merge, tymeet as retic_meet
from exc import UnimplementedException as ReticUnimplementedException
from rproxy import create_proxy as retic_create_proxy

class CastError(Exception):
    pass
class FunctionCastTypeError(CastError, TypeError):
    pass
class ObjectTypeAttributeCastError(CastError, AttributeError):
    pass

def retic_actual(v):
    if hasattr(v, '__actual__'):
        return v.__actual__
    return v

def retic_assert(bool, msg, exc=None):
    if not bool:
        if exc == None:
            exc = CastError
        raise exc(msg)

def iw(f):
    def w(val, src, trg, msg, line=None):
        x = f(val,src,trg,msg,line)
        return x
    return w

#@iw
def retic_cast(val, src, trg, msg, line=None):
    if src == trg:
        return val
    if line == None:
        line = inspect.currentframe().f_back.f_lineno
    if retic_tyinstance(trg, rtypes.Dyn):
        if retic_tyinstance(src, rtypes.Function):
            return retic_cast(val, src, retic_dynfunc(src), msg, line=line)
        else: return val
    elif retic_tyinstance(src, rtypes.Dyn):
        if retic_tyinstance(trg, rtypes.Function):
            retic_assert(callable(val), "%s at line %d" % (msg, line), exc=FunctionCastTypeError)
            return retic_cast(val, retic_dynfunc(trg), trg, msg, line=line)
        elif retic_tyinstance(trg, rtypes.Object) or retic_tyinstance(trg, rtypes.Class):
            retic_assert(retic_has_shape(val, trg.members), '%s at line %d (expected %s, has %s)' % (msg, line, trg, dir(val)), exc=ObjectTypeAttributeCastError)
            midty = trg.__class__(trg.name, {k: rtypes.Dyn for k in trg.members})
            return retic_cast(val, midty, trg, msg, line=line)
        else:
            retic_assert(retic_has_type(val, trg), "%s at line %d (expected %s, has %s)" % (msg, line, trg, val))
            return val
    elif retic_tyinstance(src, rtypes.Function) and retic_tyinstance(trg, rtypes.Function):
        retic_assert(retic_subcompat(src, trg),  "%s at line %d" % (msg, line))
        if val == exec:
            return val
        return retic_make_function_wrapper(val, src, trg, msg + "YUESS %s %s" % (src, trg), line)
    elif retic_tyinstance(src, typing.Object):
        if retic_tyinstance(trg, typing.Object):
            for m in trg.members:
                if m in src.members:
                    retic_assert(retic_subcompat(trg.members[m], src.members[m]), "%s at line %d" % (msg, line))
                else:
                    retic_assert(hasattr(val, m), "%s at line %d" % (msg, line), exc=ObjectTypeAttributeCastError)
                    retic_assert(retic_has_type(getattr(val, m), trg.members[m]), "%s at line %d" % (msg, line))
            return retic_make_proxy(val, src, trg, msg, line)
        elif retic_tyinstance(trg, typing.Function):
            if '__call__' in src.members:
                return retic_make_function_wrapper(val, src.member_type('__call__'), trg, msg, line)
            else:
                retic_assert(hasattr(val, '__call__'), "%s at line %d" % (msg, line), exc=ObjectTypeAttributeCastError)
                return retic_make_function_wrapper(val, retic_dynfunc(trg), trg, msg, line)
        else: raise ReticUnimplementedException(src, trg)
    elif retic_tyinstance(src, typing.Class):
        if retic_tyinstance(trg, typing.Class):
            for m in trg.members:
                if m in src.members:
                    assert retic_subcompat(trg.members[m], src.members[m])
                else:
                    retic_assert(hasattr(val, m), "%s at line %d" % (msg, line), exc=ObjectTypeAttributeCastError)
                    assert retic_has_type(getattr(val, m), trg.members[m]), "%s at line %d" % (msg, line)
            return retic_make_proxy(val, src, trg, msg, line)
        elif retic_tyinstance(trg, typing.Function):
            call = '__new__' if isinstance(val, type) else '__call__'
            if call in src.members:
                return retic_make_proxy(val, src.member_type(call).bind(), trg, msg, line)
            else:
                retic_assert(hasattr(val, call), "%s at line %d" % (msg, line), exc=ObjectTypeAttributeCastError)
                return retic_make_function_wrapper(val, retic_dynfunc(trg), trg, msg, line)
        else: raise ReticUnimplementedException(src, trg)
    elif any(retic_tyinstance(src, collection) and retic_tyinstance(trg, collection) \
                 for collection in [typing.Tuple, typing.List, typing.Dict, typing.Set]) and \
                 retic_subcompat(src, trg):
        #retic_assert(retic_has_type(val, trg), '%s at line %s' % (msg, line))
        return retic_make_proxy(val, src.structure(), trg.structure(), msg, line)
    elif retic_subcompat(src, trg):
        return retic_make_proxy(val, src.structure(), trg.structure(), msg, line)
    else:
        raise ReticUnimplementedException(src, trg)


_special_names = []
boo = [
    '__abs__', '__add__', '__and__', '__call__', '__cmp__', '__coerce__', 
    '__contains__', '__delitem__', '__delslice__', '__div__', '__divmod__', 
    '__eq__', '__float__', '__floordiv__', '__ge__', '__getitem__', 
    '__getslice__', '__gt__', '__hash__', '__hex__', '__iadd__', '__iand__',
    '__idiv__', '__idivmod__', '__ifloordiv__', '__ilshift__', '__imod__', 
    '__imul__', '__int__', '__invert__', '__ior__', '__ipow__', '__irshift__', 
    '__isub__', '__iter__', '__itruediv__', '__ixor__', '__le__', '__len__', 
    '__long__', '__lshift__', '__lt__', '__mod__', '__mul__', '__ne__', 
    '__neg__', '__oct__', '__or__', '__pos__', '__pow__', '__radd__', 
    '__rand__', '__rdiv__', '__rdivmod__', '__reduce__', '__reduce_ex__', 
    '__repr__', '__reversed__', '__rfloorfiv__', '__rlshift__', '__rmod__', 
    '__rmul__', '__ror__', '__rpow__', '__rrshift__', '__rshift__', '__rsub__', 
    '__rtruediv__', '__rxor__', '__setitem__', '__setslice__', '__sub__', 
    '__truediv__', '__xor__', 'next', '__nonzero__', '__str__', '__repr__'
]

def retic_proxy(val, src, meet, trg, msg, line, call=None, meta=False):
    Proxy = retic_create_proxy(val)

    typegen = isinstance(val, type) and not meta

    if typegen:
        meta = retic_proxy(val, src, meet, trg, msg, line, call=call,meta=True)
        try:
            class Proxy(val, metaclass=meta):
                def __new__(cls, *args, **kwd):
                    return call.__get__(cls)(*args, **kwd)
        except TypeError:
            class Proxy(type, metaclass=meta):
                def __new__(cls, *args, **kwd):
                    return call.__get__(cls)(*args, **kwd)
        return Proxy


    def make_meth(k):
        def method(self, *args, **kwd):
            return Proxy.__getattribute__(self,k)(*args, **kwd)
        method.__name__ = k
    for name in _special_names:
        setattr(Proxy, name, make_meth(name))
    Proxy.__actual__ = val
    Proxy.__cast__ = src, meet, trg, msg, line
    Proxy.__getattribute__ = retic_make_getattr(val, src, meet, trg, msg, line, function=call)
    Proxy.__setattr__ = retic_make_setattr(val, src, meet, trg, msg, line)
    Proxy.__delattr__ = retic_make_delattr(val, src, meet, trg, msg, line)
    if not meta:
        prox = Proxy()
    if meta:
        return Proxy
    return prox
    

def retic_check_threesome(val, src, trg, msg, line):
    if hasattr(val, '__actual__'):
        nsrc, tm, _, tmsg, tline = val.__cast__
        meet = retic_meet(tm, src, trg)
        actual = val.__actual__
    else: 
        actual = val
        meet = retic_meet(src, trg)
        nsrc = src
    retic_assert(meet.bottom_free(), msg)
    return actual, nsrc, meet 


def retic_make_function_wrapper(val, src, trg, msg, line):
    base_val, base_src, meet = retic_check_threesome(val, src, trg, msg, line)

    src_fmls = src.froms
    src_ret = src.to
    trg_fmls = trg.froms
    trg_ret = trg.to

    fml_len = max(src_fmls.len(), trg_fmls.len())
    bi = inspect.isbuiltin(base_val)    

    def wrapper(self, *args, **kwds):
        kwc = len(args)
        ckwds = {}
        if retic_pinstance(src_fmls, rtypes.NamedParameters):
            for k in kwds:
                if k in [k for k, _ in src_fmls.parameters]:
                    kwc -= 1
                    ckwds[k] = retic_cast(kwds[k], rtypes.Dyn, dict(src_fmls.parameters)[k], msg, line=line)
                else: ckwds[k] = kwds[k]
        if fml_len != -1:
            retic_assert(len(args)+len(kwds) == fml_len, '%d %d %d %s %s %s at line %d' % (len(args), len(kwds), fml_len, trg_fmls, src_fmls, msg, line))
        cargs = [ retic_mergecast(arg, trg, src, msg, line=line)\
                      for arg, trg, src in zip(args, trg_fmls.types(len(args)+len(kwds))[:kwc], src_fmls.types(len(args)+len(kwds))[:kwc]) ]
        if bi:
            if (base_val is eval or base_val is exec):
                if len(cargs) < 2 and 'globals' not in ckwds:
                    cargs.append(inspect.getouterframes(inspect.currentframe())[2][0].f_locals)
                if len(cargs) < 3 and 'locals' not in ckwds:
                    cargs.append(inspect.getouterframes(inspect.currentframe())[2][0].f_globals)
                ret = val(*cargs, **ckwds)
            elif base_val is globals:
                ret = inspect.getouterframes(inspect.currentframe())[2][0].f_globals
            elif base_val is locals:
                ret = inspect.getouterframes(inspect.currentframe())[2][0].f_locals
            else:
                # DANGEROUS
                #locals().update(inspect.getouterframes(inspect.currentframe())[2][0].f_locals)
                #globals().update(inspect.getouterframes(inspect.currentframe())[2][0].f_locals)
                ret = val(*cargs, **ckwds)
        else: ret = val(*cargs, **ckwds)
        return retic_mergecast(ret, src_ret, trg_ret, msg, line=line)

    return retic_proxy(base_val, base_src, meet, trg, msg, line, call=wrapper)

def retic_make_proxy(val, src, trg, msg, line, ext_meet=None):
    val, src, meet = retic_check_threesome(val, src, trg, msg, line)
    if isinstance(val, type):
        def construct(cls, *args, **kwd):
            c = val.__new__(val)
            prox = retic_make_proxy(c, src.instance(), trg.instance(), msg, line, meet.instance())
            prox.__init__(*args, **kwd)
            return prox
    else:
        construct = None

    return retic_proxy(val, src, meet, trg, msg, line, call=construct)
    
def retic_mergecast(val, src, trg, msg, line):
    return retic_cast(val, src, retic_merge(src, trg), msg, line)

def retic_make_getattr(obj, src, meet, trg, msg, line, function=None):
    def n_getattr(prox, attr):
        if attr == '__cast__':
            return (src, meet, trg, msg, line)
        elif attr == '__actual__':
            return obj
        elif attr == '__getstate__':
            if hasattr(obj, '__getstate__'):
                return obj.__getstate__
            else: return lambda: obj
        elif attr == '__new__':
            return function
        elif function:
            if attr == '__call__':
                return function.__get__(prox)
        val = getattr(obj, attr)
        if inspect.ismethod(val) and val.__self__ is obj:
            val = val.__func__.__get__(prox)
        lsrc = src.member_type(attr, rtypes.Dyn)
        lmeet = meet.member_type(attr, rtypes.Dyn)
        ltrg = trg.member_type(attr, rtypes.Dyn)
        return retic_mergecast(retic_mergecast(val, lsrc, lmeet, msg, line=line), lmeet, ltrg, msg, line=line)
    return n_getattr

def retic_make_setattr(obj, src, meet, trg, msg, line):
    def n_setattr(prox, attr, val):
        lsrc = src.member_type(attr, rtypes.Dyn)
        lmeet = meet.member_type(attr, rtypes.Dyn)
        ltrg = trg.member_type(attr, rtypes.Dyn)
        setattr(obj, attr, retic_mergecast(retic_mergecast(val, ltrg, lmeet, msg, line),
                                           lmeet, lsrc, msg, line))
    return n_setattr

def retic_make_delattr(obj, src, meet, trg, msg, line):
    def n_delattr(prox, attr):
        lmeet = meet.member_type(attr, rtypes.Dyn)
        if retic_tyinstance(lmeet, rtypes.Dyn):
            delattr(obj, attr)
        else: retic_error('%s at line %s' % (msg, line))
    return n_delattr
        
def retic_dynfunc(ty):
    return rtypes.Function(rtypes.DynParameters, rtypes.Dyn)

def retic_check(val, trg, msg):
    return val

def retic_error(msg):
    assert False, "%s at line %d" % (msg, inspect.currentframe().f_back.f_lineno)
