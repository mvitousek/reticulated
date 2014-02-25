import typing, inspect, rtypes
from typing import tyinstance as retic_tyinstance, has_type as retic_has_type, subcompat as retic_subcompat,\
    has_shape as retic_has_shape
from exc import UnimplementedException as ReticUnimplementedException

class CastError(Exception):
    pass
class FunctionCastTypeError(CastError, TypeError):
    pass
class ClassTypeAttributeError(CastError, AttributeError):
    pass

def retic_assert(bool, msg, exc=None):
    if not bool:
        if exc == None:
            exc = CastError
        raise exc(msg)

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
            retic_assert(retic_has_shape(val, trg.members), '%s at line %d (expected %s)' % (msg, line, trg), exc=ClassTypeAttributeError)
            midty = trg.__class__(trg.name, {k: rtypes.Dyn for k in trg.members})
            return retic_cast(val, midty, trg, msg, line=line)
        else:
            assert retic_has_type(val, trg), "%s at line %d (expected %s)" % (msg, line, trg)
            return val
    elif retic_tyinstance(src, rtypes.Function) and retic_tyinstance(trg, rtypes.Function):
        assert retic_subcompat(src, trg),  "%s at line %d" % (msg, line)
        return retic_make_function_wrapper(val, src.froms, trg.froms, src.to, trg.to, msg, line)
    elif retic_tyinstance(src, typing.Object) and retic_tyinstance(trg, typing.Object):
        for m in trg.members:
            if m in src.members:
                assert retic_subcompat(trg.members[m], src.members[m])
            else:
                retic_assert(hasattr(val, m), "%s at line %d" % (msg, line), exc=ClassTypeAttributeError)
                assert retic_has_type(getattr(val, m), trg.members[m]), "%s at line %d" % (msg, line)
        return retic_make_proxy(val, src.members, trg.members, line)
    elif retic_subcompat(src, trg):
        return retic_make_proxy(val, src.structure(), trg.structure(), line)
    else:
        raise ReticUnimplementedException(src, trg)

def retic_make_function_wrapper(fun, src_fmls, trg_fmls, src_ret, trg_ret, msg, line):
    fml_len = max(src_fmls.len(), trg_fmls.len())
    def wrapper(*args, **kwds):
        kwc = 0
        ckwds = {}
        if pinstance(trg_fmls, retic.NamedParameters):
            for k in kwds:
                if k in [k for k, _ in src_fmls.parameters]:
                    kwc += 1
                    ckwds[k] = retic_cast(kwds[k], Dyn, dict(src_fmls.parameters)[k], msg, line=line)
                else ckwds[k] = kwds[k]
        if fml_len != -1:
            assert len(args) == fml_len, '%s at line %d' % (msg, line)
        cargs = [ retic_cast(arg, trg, src, msg, line=line)\
                      for arg, trg, src in zip(args, trg_fmls.types(len(args))[:-kwc], src_fmls.types(len(args))[:-kwc]) ]
        ret = fun(*cargs, **kwds)
        return retic_cast(ret, src_ret, trg_ret, msg, line=line)
    wrapper.__name__ = fun.__name__ if hasattr(fun, '__name__') else 'function'
    return wrapper

def retic_make_proxy(obj, src, trg, line):
    class Proxy:
        pass
    Proxy.__getattribute__ = retic_make_getattr(obj, src, trg, line)
    Proxy.__setattr__ = retic_make_setattr(obj, src, trg, line)
    Proxy.__delattr__ = retic_make_delattr(obj, src, trg, line)
    return Proxy()

def retic_make_getattr(obj, src, trg, line):
    def n_getattr(prox, attr):
        val = getattr(obj, attr)
        lsrc = src.get(attr, rtypes.Dyn)
        ltrg = trg.get(attr, rtypes.Dyn)
        return retic_cast(val, lsrc, ltrg, 'error', line=line)
    return n_getattr

def retic_make_setattr(obj, src, trg, line):
    def n_setattr(prox, attr, val):
        lsrc = src.get(attr, rtypes.Dyn)
        ltrg = trg.get(attr, rtypes.Dyn)
        setattr(obj, attr, retic_cast(val, ltrg, lsrc, 'error', line=line))
    return n_setattr

def retic_make_delattr(obj, src, trg, line):
    def n_delattr(prox, attr):
        lsrc = src.get(attr, rtypes.Dyn)
        ltrg = trg.get(attr, rtypes.Dyn)
        if retic_tyinstance(lsrc, rtypes.Dyn) and retic_tyinstance(ltrg, rtypes.Dyn):
            delattr(obj, attr)
        else: retic_error('undeleteable')
    return n_delattr
        
def retic_dynfunc(ty):
    return rtypes.Function(rtypes.DynParameters, rtypes.Dyn)

def retic_check(val, trg, msg):
    return val

def retic_error(msg):
    assert False, "%s at line %d" % (msg, inspect.currentframe().f_back.f_lineno)
