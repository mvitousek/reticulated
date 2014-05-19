from typing import has_type as retic_has_type, warn as retic_warn, tyinstance as retic_tyinstance, has_shape as retic_has_shape, subcompat as retic_subcompat, pinstance as retic_pinstance
from relations import tymeet as retic_meet, Bot as ReticBot, merge as retic_merge
from exc import UnimplementedException as ReticUnimplementedException
import typing, inspect, guarded, rtypes
from rproxy import create_proxy as retic_create_proxy

class InternalTypeError(Exception):
    pass

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

def retic_strengthen_monotonics(value, new, line):
    new = new.copy()
    if not hasattr(value, '__monotonics__'):
        value.__monotonics__ = new
    else:
        for attr in new:
            if attr in value.__monotonics__:
                try:
                    value.__monotonics__[attr] = retic_meet([new[attr], 
                                                               value.__monotonics__[attr]])
                except ReticBot:
                    assert False, "References with incompatible types referring to same object at line %d" % (msg, line)
            else:
                value.__monotonics__[attr] = new[attr]

def retic_monotonic_cast(value, src, trg, members, msg, line):
    if not retic_can_be_monotonic(value, line):
        return retic_make_proxy(value, src, trg, msg, line)
    monos = {}
    updates = {}
    def update(loc, mem, dict):
        if loc in dict:
            dict[loc][mem] = members[mem]
        else:
            dict[loc] = {mem : members[mem]}
    mro = [value] + type.mro(value.__class__)
    for mem in members:
        for loc in mro:
            update(loc, mem, monos)
            if mem in loc.__dict__:
                update(loc,mem,updates)
                break
        else: #If no break occurred on internal loop
            raise InternalTypeError
    for location in monos:
        monotonics = monos[location]
        upd = updates.get(location, [])

        for mem in upd:
            try:
                mem_val = getattr(location, mem)
                if hasattr(location, '__monotonics__') and mem in location.__monotonics__:
                    srcty = location.__monotonics__[mem]
                else: srcty = typing.Dyn
                trgty = retic_meet([srcty, upd[mem]])
                if not trgty.bottom_free():
                    raise CastError('%s at line %s' % (msg, line))
                new_mem_val = retic_cast(mem_val, srcty, trgty, msg, line=line)
                setattr(location, mem, new_mem_val)
            except ReticBot:
                raise InternalTypeError
            except AttributeError:
                retic_warn('Unable to modify %s attribute of value %s at line %d' % (mem, location, line), 0)
                continue
        retic_strengthen_monotonics(location, monotonics, line=line)
        
        if retic_can_be_monotonic(location, line):
            if not retic_monotonic_installed(location.__class__):
                retic_install_setter(location, line)
                retic_install_deleter(location, line)
                retic_install_getter(location, line)
        else: print('Unable to monotonically specify')
    return value

# Casts 
def retic_cast(val, src, trg, msg, line=None):
    if src == trg:
        return val
    if line == None:
        line = inspect.currentframe().f_back.f_lineno
    if retic_tyinstance(trg, rtypes.Dyn):
        if retic_tyinstance(src, rtypes.Function):
            return retic_cast(val, src, retic_dynfunc(src), msg, line=line)
        elif retic_tyinstance(src, rtypes.Object) or retic_tyinstance(src, rtypes.Class):
            midty = src.__class__(src.name, {k: rtypes.Dyn for k in src.members})
            return retic_cast(val, src, midty, msg, line=line)
        else: return val
    elif retic_tyinstance(src, rtypes.Dyn):
        if retic_tyinstance(trg, rtypes.Function):
            retic_assert(callable(val), "%s at line %d" % (msg, line), exc=FunctionCastTypeError)
            return retic_cast(val, rtypes.Function(rtypes.DynParameters, rtypes.Dyn), trg, msg, line=line)
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
        return retic_make_function_wrapper(val, src, trg, msg, line)
    elif retic_tyinstance(src, typing.Object):
        if retic_tyinstance(trg, typing.Object):
            for m in trg.members:
                if m in src.members:
                    retic_assert(retic_subcompat(trg.members[m], src.members[m]), "%s at line %d" % (msg, line))
                else:
                    retic_assert(hasattr(val, m), "%s at line %d" % (msg, line), exc=ObjectTypeAttributeCastError)
                    retic_assert(retic_has_type(getattr(val, m), trg.members[m]), "%s at line %d" % (msg, line))
            return retic_monotonic_cast(val, src, trg, trg.members, msg, line)
        elif retic_tyinstance(trg, typing.Function):
            if '__call__' in src.members:
                nsrc = src.member_type('__call__')
            else:
                retic_assert(hasattr(val, '__call__'), "%s at line %d" % (msg, line), exc=ObjectTypeAttributeCastError)
                nsrc = Function(DynParameters, Dyn)
            val = retic_monotonic_cast(val, nsrc, trg, {'__call__': trg}, msg, line)
            return retic_make_function_wrapper(val, nsrc, trg, msg, line)
        else: raise ReticUnimplementedException(src, trg)
    elif retic_tyinstance(src, typing.Class):
        if retic_tyinstance(trg, typing.Class):
            for m in trg.members:
                if m in src.members:
                    retic_assert(retic_subcompat(trg.members[m], src.members[m]), "%s at line %d" % (msg, line))
                else:
                    retic_assert(hasattr(val, m), "%s at line %d" % (msg, line), exc=ObjectTypeAttributeCastError)
                    retic_assert(retic_has_type(getattr(val, m), trg.members[m]), "%s at line %d" % (msg, line))
            return retic_monotonic_cast(val, src, trg, trg.members, msg, line)
        elif retic_tyinstance(trg, typing.Function):
            call = '__new__' if isinstance(val, type) else '__call__'
            if call in src.members:
                nsrc = src.member_type(call).bind()
            else:
                retic_assert(hasattr(val, call), "%s at line %d" % (msg, line), exc=ObjectTypeAttributeCastError)
                nsrc = Function(DynParameters, Dyn)
            val = retic_monotonic_cast(val, nsrc, trg, {call: trg}, msg, line)
            return retic_make_function_wrapper(val, nsrc, trg, msg, line)
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
"""
def retic_cast(val, src, trg, msg, line=None):
    if line == None:
        line = inspect.currentframe().f_back.f_lineno
    try:
        if typing.tyinstance(src, typing.Record) and typing.tyinstance(trg, typing.Record):
            retic_monotonic_cast(val, trg.members, line)
            return val
        

        if src == trg:
            return val
        elif typing.tyinstance(trg, typing.Dyn):
            return ReticInjected(val, src)
        elif typing.tyinstance(src, typing.Dyn):
            if type(val) == ReticInjected:
                if type(val.ty) == type(trg):
                    return val.project(trg, msg, line)
                else:
                    assert False, "%s at line %d" % (msg, line)
            else:
                retic_setup_type(val, trg, line=line)                
                return val
        elif type(src) != type(trg):
            assert False, "%s at line %d" % (msg, line)
        elif typing.tyinstance(src, typing.Record) and typing.tyinstance(trg, typing.Record):
            retic_monotonic_cast(val, trg.members, line)
            return val
        else: raise ReticUnimplementedException('Unhandled cast')
    except InternalTypeError:
        assert False, "%s at line %d" % (msg, line)
"""
def retic_check(val, trg, msg, line=inspect.currentframe().f_back.f_lineno):
    # This needs to be a NAIVE SUPERTYPE check, MAYBE?
    #assert retic_has_type(val, trg), "%s at line %d" % (msg, inspect.currentframe().f_back.f_lineno)
    return val

def retic_error(msg, line=inspect.currentframe().f_back.f_lineno):
    assert False, "%s at line %d" % (msg, line)

def retic_monotonic_installed(value):
    return hasattr(value, '__fastsetattr__')

def retic_can_be_monotonic(value, line):
    # Check for typical issues
    if value.__class__ == object:
        retic_warn('Line %d: %s is a direct instance of the object class. Direct instances of the <object> class do not support monotonicity.' % (line, value),0)
        return False
    elif value.__class__ == type:
        retic_warn('Line %d: Class <%s> does not have a metaclass, and Reticulated was unable to insert one statically. '  % (line, value.__name__) +  \
                 'Classes without metaclasses do not support monotonicity',0)
        return False
    else:
        try:
            value.__class__.__getattribute__ = value.__class__.__getattribute__
            return True
        except TypeError:
            retic_warn('Line %d: %s cannot be made monotonic.' % (line, value), 0)

def retic_install_getter(value, line):
    getter = value.__class__.__getattribute__
    value.__class__.__fastgetattr__ = getter
    def deep_hasattr(obj, attr): # Using hasattr in new_getter results in infinite loop
        try: 
            getter(obj, attr)
            return True
        except AttributeError:
            return False
    def new_getter(obj, attr):
        if deep_hasattr(obj, attr) and attr in getter(obj, '__monotonics__'):
            return retic_cast(getter(obj, attr), getter(obj, '__monotonics__')[attr], typing.Dyn, 'Cast failure', line=line)
        else: return getter(obj, attr)
    value.__class__.__getattribute__ = new_getter
    def typed_getter(obj, attr, ty):
        if deep_hasattr(obj, '__monotonics__') and attr in getter(obj, '__monotonics__'):
            return retic_cast(getter(obj, attr), getter(obj, '__monotonics__')[attr], ty, 'Cast failure', line=line)
        elif attr in ['__getattribute__', '__getattr_attype__', '__fastgetattr__', '__setattr__', '__setattr_attype__', '__fastsetattr__']:
            return getter(obj, attr)
        else: raise UnexpectedTypeError('Typed-getting an inappropriate value')
    value.__class__.__getattr_attype__ = typed_getter

def retic_install_setter(value, line):
    setter = value.__class__.__setattr__
    value.__class__.__fastsetattr__ = setter
    def new_setter(obj, attr, val):
        if hasattr(obj, '__monotonics__') and attr in obj.__monotonics__:
            val = retic_cast(val, typing.Dyn, obj.__monotonics__[attr], 'Cast failure', line=line)
        setter(obj, attr, val)
    value.__class__.__setattr__ = new_setter
    def typed_setter(obj, attr, val, ty):
        if hasattr(obj, '__monotonics__') and attr in obj.__monotonics__:
            val = retic_cast(val, ty, obj.__monotonics__[attr], 'Cast failure', line=line)
            setter(obj, attr, val)
        else: raise UnexpectedTypeError('Typed-setting an inappropriate value')
    value.__class__.__setattr_attype__ = typed_setter
    
def retic_install_deleter(value, line):
    deleter = value.__class__.__delattr__
    def new_deleter(obj, attr):
        if hasattr(obj, '__monotonics__') and attr in obj.__monotonics__:
            assert False, "Attempting to delete monotonic attribute at line %d" % line
        else: deleter(obj, attr)
    value.__class__.__delattr__ = new_deleter


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

    Proxy.__actual__ = val
    Proxy.__cast__ = src, meet, trg, msg, line
    Proxy.__getattribute__ = retic_make_getattr(val, src, meet, trg, msg, line, function=call)
    Proxy.__setattr__ = retic_make_setattr(val, src, meet, trg, msg, line)
    Proxy.__delattr__ = retic_make_delattr(val, src, meet, trg, msg, line)
    if not meta:
        return Proxy()
    else:
        return Proxy

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

def retic_get_actual(val):
    if hasattr(val, '__actual__'):
        return val.__actual__
    else: return val

def retic_make_function_wrapper(val, src, trg, msg, line):
    base_val, base_src, meet = retic_check_threesome(val, src, trg, msg, line)

    src_fmls = src.froms
    src_ret = src.to
    trg_fmls = trg.froms
    trg_ret = trg.to

    fml_len = max(src_fmls.len(), trg_fmls.len())
    bi = inspect.isbuiltin(base_val) or (hasattr(base_val, '__self__') and not hasattr(base_val, '__func__'))

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
                stripped_cargs = [retic_get_actual(val) for val in cargs]
                stripped_ckwds = {k: retic_get_actual(ckwds[k]) for k in ckwds}
                ret = val(*stripped_cargs, **stripped_ckwds)
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
        elif hasattr(val, '__self__'):
            val = retic_make_function_wrapper(val, rtypes.Dyn, rtypes.Dyn, msg, line)
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

def retic_getattr_static(val, attr, ty):
    if retic_monotonic_installed(val):
        return val.__fastgetattr__(attr)
    else: return retic_check(getattr(val, attr), ty, 'Attribute in non-object value ill-typed', line=inspect.currentframe().f_back.f_lineno)

def retic_getattr_dynamic(val, attr, ty):
    if retic_monotonic_installed(val):
        return val.__getattr_attype__(attr, ty)
    else: return retic_check(getattr(val, attr), ty, 'Attribute in non-object value ill-typed', line=inspect.currentframe().f_back.f_lineno)        

def retic_setattr_static(val, attr, written, ty):
    if retic_monotonic_installed(val):
        val.__fastsetattr__(attr, written)
    else: # If val is not a monotonic object, fall back to casts-as-check
        retic_check(written, ty, 'Attribute in non-object value ill-typed', line=inspect.currentframe().f_back.f_lineno)
        setattr(val, attr, written)

def retic_setattr_dynamic(val, attr, written, ty):
    if retic_monotonic_installed(val):
        val.__setattr_attype__(attr, written, ty)
    else: 
        retic_check(written, ty, 'Attribute in non-object value ill-typed', line=inspect.currentframe().f_back.f_lineno)
        setattr(val, attr, written)
