import typing
from typing import tyinstance as retic_instance, has_type as retic_has_type, subcompat as retic_subcompat
from exc import UnimplementedException as ReticUnimplementedException


def retic_cast(val, src, trg, msg):
    line = inspect.currentframe().f_back.f_lineno
    if retic_instance(trg, Dyn):
        if retic_instance(src, typing.Function):
            return retic_cast(val, src, retic_dynfunc(src), msg)
        else: return val
    elif retic_instance(src, Dyn):
        if retic_instance(trg, typing.Function):
            return retic_cast(val, retic_dynfunc(trg), trg, msg)
        else:
            assert retic_has_type(val, trg), "%s at line %d" % (msg, line)
    elif retic_tyinstance(src, Function) and retic_tyinstance(trg, Function):
        assert all(retic_subcompat(b, a) for (a, b) in zip(src.froms, trg.froms)) and \
            retic_subcompat(src.to, trg.to),  "%s at line %d" % (msg, line)
        return retic_make_function_wrapper(val, src.froms, trg.froms, src.to, trg.to, line)
    elif retic_tyinstance(src, Object) and retic_tyinstance(trg, Object):
        for m in trg.members:
            if m in src.members:
                assert retic_subcompat(trg.members[m], src.members[m])
            else:
                assert hasattr(val, m), "%s at line %d" % (msg, line)
                assert retic_has_type(getattr(val, m), trg.members[m]), "%s at line %d" % (msg, line)
        return retic_make_proxy(val, src, trg, line)
    elif retic_subcompat(trg, src):
        return val
    else:
        raise ReticUnimplementedException(src, trg)

def retic_make_function_wrapper(fun, src_fmls, trg_fmls, src_ret, trg_ret, line):
    assert len(src_fmls) == len(trg_fmls)
    def wrapper(*args):
        assert len(args) == len(trg_fmls), 'Incorrect number of arguments to function at line %d' % line
        cargs = [ retic_cast(arg, trg, src, 'Parameter of incorrect type', line=line) for arg, trg, src in zip(args, trg_fmls, src_fmls) ]
        ret = fun(*cargs)
        return retic_cast(ret, src_ret, trg_ret)
    wrapper.__name__ = fun.__name__
    return wrapper

def retic_make_proxy(obj, src, trg, line):
    raise ReticUnimplementedException('no proxies yet. would be a good idea huh')
            
def retic_dynfunc(ty):
    return typing.Function([Dyn for _ in ty.froms], Dyn)

def retic_check(val, src, trg, msg):
    return val

def retic_error(msg):
    assert False, "%s at line %d" % (msg, inspect.currentframe().f_back.f_lineno)
