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

def retic_make_function_wrapper(fun, src, trg, msg, line):
    if hasattr(fun, '__actual__'):
        base_src, omeet, otrg, omsg, oline = fun.__cast__
        base_fun = fun.__actual__
        meet = retic_meet(omeet, src, trg)
        retic_assert(meet.bottom_free(), [omeet, src, trg, meet]) #'%s at line %s' % (msg, line))
    else:
        base_src = src
        base_fun = fun
        meet = retic_meet(src, trg)


    src_fmls = src.froms
    src_ret = src.to
    trg_fmls = trg.froms
    trg_ret = trg.to

    fml_len = max(src_fmls.len(), trg_fmls.len())
    bi = inspect.isbuiltin(base_fun)    

    def wrapper(self, *args, **kwds):
        kwc = len(args)
        ckwds = {}
        if retic_pinstance(trg_fmls, rtypes.NamedParameters):
            for k in kwds:
                if k in [k for k, _ in src_fmls.parameters]:
                    kwc -= 1
                    ckwds[k] = retic_cast(kwds[k], Dyn, dict(src_fmls.parameters)[k], msg, line=line)
                else: ckwds[k] = kwds[k]
        if fml_len != -1:
            retic_assert(len(args) == fml_len, '%d %d %d %s %s %s at line %d' % (len(args), len(kwds), fml_len, trg_fmls, src_fmls, msg, line))
        cargs = [ retic_mergecast(arg, trg, src, msg, line=line)\
                      for arg, trg, src in zip(args, trg_fmls.types(len(args))[:kwc], src_fmls.types(len(args))[:kwc]) ]
        if bi:
            if (base_fun is eval or base_fun is exec):
                if len(cargs) < 2 and 'globals' not in ckwds:
                    cargs.append(inspect.getouterframes(inspect.currentframe())[2][0].f_locals)
                if len(cargs) < 3 and 'locals' not in ckwds:
                    cargs.append(inspect.getouterframes(inspect.currentframe())[2][0].f_globals)
                ret = fun(*cargs, **ckwds)
            elif base_fun is globals:
                ret = inspect.getouterframes(inspect.currentframe())[2][0].f_globals
            elif base_fun is locals:
                ret = inspect.getouterframes(inspect.currentframe())[2][0].f_locals
            else:
                # DANGEROUS
                #locals().update(inspect.getouterframes(inspect.currentframe())[2][0].f_locals)
                #globals().update(inspect.getouterframes(inspect.currentframe())[2][0].f_locals)
                ret = fun(*cargs, **ckwds)
        else: ret = fun(*cargs, **ckwds)
        return retic_mergecast(ret, src_ret, trg_ret, msg, line=line)

    wrapper.__name__ = fun.__name__ if hasattr(fun, '__name__') else 'function'

    Proxy = retic_create_proxy(fun)
    Proxy.__name__ = 'FunctionProxy'
    Proxy.__call__ = lambda self, *args, **kwd: self.__call__(*args, **kwd)
    Proxy.__getattribute__ = retic_make_getattr(base_fun, base_src, meet, trg, msg, line, function=wrapper)
    Proxy.__setattr__ = retic_make_setattr(base_fun, base_src, meet, trg, msg, line)
    Proxy.__delattr__ = retic_make_delattr(base_fun, base_src, meet, trg, msg, line)

    return Proxy()

def retic_make_proxy(obj, src, trg, msg, line, ext_meet=None):
    if hasattr(obj, '__actual__'):
        osrc, omeet, otrg, omsg, oline = obj.__cast__
        obj = obj.__actual__
        meet = retic_meet(omeet, src, trg, ext_meet if ext_meet else rtypes.Dyn)
        retic_assert(meet.bottom_free(), [omeet, src, trg, ext_meet, meet])
        src = osrc
    else: 
        meet = retic_meet(src, trg, ext_meet if ext_meet else rtypes.Dyn)
        retic_assert(meet.bottom_free(), [src, trg, ext_meet, meet])

    Proxy = retic_create_proxy(obj)

    if isinstance(obj, type):
        def construct(self, *args, **kwd):
            c = obj.__new__(obj)
            prox = retic_make_proxy(c, src.instance(), trg.instance(), msg, line, meet.instance())
            prox.__init__(*args, **kwd)
            return prox
    else: construct = None
        
    Proxy.__getattribute__ = retic_make_getattr(obj, src, meet, trg, msg, line, function=construct)
    Proxy.__setattr__ = retic_make_setattr(obj, src, meet, trg, msg, line)
    Proxy.__delattr__ = retic_make_delattr(obj, src, meet, trg, msg, line)
    return Proxy()
    
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
