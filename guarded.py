import typing, inspect
from typing import tyinstance as retic_tyinstance, has_type as retic_has_type, subcompat as retic_subcompat
from exc import UnimplementedException as ReticUnimplementedException

def retic_cast(val, src, trg, msg, line=None):
    if line == None:
        line = inspect.currentframe().f_back.f_lineno
    if retic_tyinstance(trg, typing.Dyn):
        if retic_tyinstance(src, typing.Function):
            return retic_cast(val, src, retic_dynfunc(src), msg)
        else: return val
    elif retic_tyinstance(src, typing.Dyn):
        if retic_tyinstance(trg, typing.Function):
            return retic_cast(val, retic_dynfunc(trg), trg, msg)
        else:
            assert retic_has_type(val, trg), "%s at line %d" % (msg, line)
            return val
    elif retic_tyinstance(src, typing.Function) and retic_tyinstance(trg, typing.Function):
        assert all(retic_subcompat(b, a) for (a, b) in zip(src.froms, trg.froms)) and \
            retic_subcompat(src.to, trg.to),  "%s at line %d" % (msg, line)
        return retic_make_function_wrapper(val, src.froms, trg.froms, src.to, trg.to, line)
    elif retic_tyinstance(src, typing.Record) and retic_tyinstance(trg, typing.Record):
        for m in trg.members:
            if m in src.members:
                assert retic_subcompat(trg.members[m], src.members[m])
            else:
                assert hasattr(val, m), "%s at line %d" % (msg, line)
                assert retic_has_type(getattr(val, m), trg.members[m]), "%s at line %d" % (msg, line)
        return retic_make_proxy(val, src.members, trg.members, line)
    elif retic_subcompat(src, trg):
        return retic_make_proxy(val, src.structure(), trg.structure(), line)
    else:
        raise ReticUnimplementedException(src, trg)

def retic_make_function_wrapper(fun, src_fmls, trg_fmls, src_ret, trg_ret, line):
    assert len(src_fmls) == len(trg_fmls)
    def wrapper(*args, **kwds):
        assert len(args) == len(trg_fmls), 'Incorrect number of arguments to function at line %d' % line
        cargs = [ retic_cast(arg, trg, src, 'Parameter of incorrect type', line=line) for arg, trg, src in zip(args, trg_fmls, src_fmls) ]
        ret = fun(*cargs, **kwds)
        return retic_cast(ret, src_ret, trg_ret, 'a')
    wrapper.__name__ = fun.__name__
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
        lsrc = src.get(attr, typing.Dyn)
        ltrg = trg.get(attr, typing.Dyn)
        return retic_cast(val, lsrc, ltrg, 'error')
    return n_getattr

def retic_make_setattr(obj, src, trg, line):
    def n_setattr(prox, attr, val):
        lsrc = src.get(attr, typing.Dyn)
        ltrg = trg.get(attr, typing.Dyn)
        setattr(obj, attr, retic_cast(val, ltrg, lsrc, 'error'))
    return n_setattr

def retic_make_delattr(obj, src, trg, line):
    def n_delattr(prox, attr):
        lsrc = src.get(attr, typing.Dyn)
        ltrg = trg.get(attr, typing.Dyn)
        if retic_tyinstance(lsrc, typing.Dyn) and retic_tyinstance(ltrg, Dyn):
            delattr(obj, attr)
        else: retic_error('undeleteable')
    return n_delattr
        
def retic_dynfunc(ty):
    return typing.Function([typing.Dyn for _ in ty.froms], typing.Dyn)

def retic_check(val, src, trg, msg):
    return val

def retic_error(msg):
    assert False, "%s at line %d" % (msg, inspect.currentframe().f_back.f_lineno)
