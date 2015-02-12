from .typing import has_type as retic_has_type, warn as retic_warn, tyinstance as retic_tyinstance, has_shape as retic_has_shape, subcompat as retic_subcompat, pinstance as retic_pinstance
from .relations import n_info_join, info_join, Bot as ReticBot, merge as retic_merge
from .exc import UnimplementedException as ReticUnimplementedException, RuntimeTypeError
import inspect
from . import typing, guarded, rtypes, mono_datastructures
from .rproxy import create_proxy as retic_create_proxy

class InternalTypeError(Exception):
    pass

class CastError(RuntimeTypeError):
    pass
class FunctionCastTypeError(CastError, TypeError):
    pass
class ObjectTypeAttributeCastError(CastError, AttributeError):
    pass

def retic_assert(bool, val, msg, exc=None):
    if not bool:
        if exc == None:
            exc = CastError
        raise exc(msg % val)

def retic_strengthen_monotonics(value, new, msg, line):
    new = new.copy()
    if '__monotonics__' not in value.__dict__:
        value.__monotonics__ = new
    else:
        for attr in new:
            if attr in value.__monotonics__:
                join = info_join(new[attr], value.__monotonics__[attr])
                if join.top_free():
                    value.__monotonics__[attr] = join
                else:
                    retic_assert(False, val, msg)
            else:
                value.__monotonics__[attr] = new[attr]

def retic_can_set(value, mem):
    try:
        setattr(value, mem, getattr(value, mem))
        return True
    except:
        return False

def retic_monotonic_cast(value, src, trg, members, msg, line):
    if not retic_can_be_monotonic(value, line):
        #return retic_make_proxy(value, src, trg, msg, line)
        return value
    monos = {}
    updates = {}
    def update(loc, mem, dict):
        if True: #At this point, we always put things in the value
            loc = 'SRC'   
        if loc in dict:
            dict[loc][mem] = members[mem]
        else:
            dict[loc] = {mem : members[mem]}
    mro = [value] + type.mro(value.__class__)
    for mem in members:
        if inspect.ismethod(getattr(value, mem)) or \
           inspect.isclass(value) and inspect.isfunction(getattr(value, mem)) or\
           hasattr(getattr(value, mem), '__self__'):
            update(value, mem, monos)
            update(value, mem, updates)
            #print('upd8', mem, value)
        else:
            for loc in mro:
                update(loc, mem, monos)
                if mem in loc.__dict__:
                    update(loc,mem,updates)
                    #print('upd8', mem, loc, getattr(value, mem))
                    break
            else: #If no break occurred on internal loop
                raise InternalTypeError(mem, line, msg)
    for location in monos:
        monotonics = monos[location]
        upd = updates.get(location, [])

        if location == 'SRC':
            location = value

        for mem in upd:
            try:
                mem_val = getattr(location, mem)
                if '__monotonics__' in location.__dict__ and mem in location.__monotonics__:
                    srcty = location.__monotonics__[mem]
                else: srcty = typing.Dyn
                trgty = info_join(srcty, upd[mem])
                if not trgty.top_free():
                    raise CastError('%s at line %s %s %s %s %s' % (msg, line, location, mem, srcty, upd[mem]))
                new_mem_val = retic_cast(mem_val, srcty, trgty, msg, line=line)
                #print(mro, monos.keys(), mem, location.__monotonics__)
                setattr(location, mem, new_mem_val)
            except AttributeError:
                retic_warn('Unable to modify %s attribute of value %s at line %d' % (mem, location, line), 0)
                continue
        
        if retic_can_be_monotonic(location, line):
            if not retic_monotonic_installed(location.__class__):
                retic_install_setter(location, line)
                retic_install_deleter(location, line)
                retic_install_getter(location, line)
            retic_strengthen_monotonics(location, monotonics, msg, line)
        else: pass#print('Unable to monotonically specify', location)
    return value

def retic_dyn_projection(ty):
    if retic_tyinstance(ty, rtypes.Function):
        return rtypes.Function(rtypes.DynParameters, rtypes.Dyn)
    elif retic_tyinstance(ty, rtypes.List):
        return rtypes.List(Dyn)
    elif retic_tyinstance(ty, rtypes.Class):
        return rtypes.Class(ty.name, 
                            {k: rtypes.Dyn for k in ty.members},
                            {k: rtypes.Dyn for k in ty.instance_members})
    elif retic_tyinstance(ty, rtypes.Object):
        return rtypes.Object(ty.name, 
                             {k: rtypes.Dyn for k in ty.members})
    elif retic_tyinstance(ty, rtypes.Structural):
        return retic_dyn_projection(ty.structure())
    else:
        return ty

def retic_inject(val, trg, msg, line):
    if retic_tyinstance(trg, rtypes.Function):
        retic_assert(callable(val), val, msg, exc=FunctionCastTypeError)
    elif retic_tyinstance(trg, rtypes.List):
        retic_assert(isinstance(val, list), msg)
    elif retic_tyinstance(trg, rtypes.Class) or retic_tyinstance(trg, rtypes.Object):
        retic_assert(retic_has_shape(val, trg.members), val, msg, exc=ObjectTypeAttributeCastError)
    elif retic_tyinstance(trg, rtypes.Structural):
        retic_inject(val, trg.structure(), msg, line)
    else:
        retic_assert(retic_has_type(val, trg), val, msg)
    

# Casts 
def retic_cast(val, src, trg, msg, line=None):
    if src == trg:
        return val
    if line == None:
        line = inspect.currentframe().f_back.f_lineno
    if retic_tyinstance(trg, rtypes.Dyn):
        trg = retic_dyn_projection(src)
        return retic_cast(val, src, trg, msg, line=line)
    elif retic_tyinstance(src, rtypes.Dyn):
        src = retic_dyn_projection(trg)
        retic_inject(val, src, msg, line)
        return retic_cast(val, src, trg, msg, line=line)
    elif retic_tyinstance(src, rtypes.Function) and retic_tyinstance(trg, rtypes.Function):
        retic_assert(retic_subcompat(src, trg), val, msg)
        if val == exec:
            return val
        return retic_make_function_wrapper(val, src, trg, msg, line)
    elif retic_tyinstance(trg, typing.List):
        if not isinstance(val, mono_datastructures.MonoList):
            if retic_tyinstance(src, typing.List):
                ty = src.type
            else: ty = Dyn
            val = mono_datastructures.MonoList(val, error=msg, line=line, type=ty)
        val.__monotonic_cast__(trg.type, msg, line)
        return val
    elif retic_tyinstance(src, typing.Object):
        if retic_tyinstance(trg, typing.Object):
            for m in trg.members:
                if m in src.members:
                    retic_assert(retic_subcompat(trg.members[m], src.members[m]), val, msg)
                else:
                    retic_assert(hasattr(val, m), msg, exc=ObjectTypeAttributeCastError)
                    retic_assert(retic_has_type(getattr(val, m), trg.members[m]), val, msg)
            return retic_monotonic_cast(val, src, trg, trg.members, msg, line)
        elif retic_tyinstance(trg, typing.Function):
            if '__call__' in src.members:
                nsrc = src.member_type('__call__')
            else:
                retic_assert(hasattr(val, '__call__'), val, msg, exc=ObjectTypeAttributeCastError)
                nsrc = rtypes.Function(rtypes.DynParameters, rtypes.Dyn)
            val = retic_monotonic_cast(val, nsrc, trg, {'__call__': trg}, msg, line)
            return retic_make_function_wrapper(val, nsrc, trg, msg, line)
        elif retic_tyinstance(trg, rtypes.Structural):
            return retic_cast(val, src, trg.structure(), msg, line=line)
        else: raise ReticUnimplementedException(src, trg)
    elif retic_tyinstance(src, typing.Class):
        if retic_tyinstance(trg, typing.Class):
            for m in trg.members:
                if m in src.members:
                    retic_assert(retic_subcompat(trg.members[m], src.members[m]), val, msg)
                else:
                    retic_assert(hasattr(val, m), val, msg, exc=ObjectTypeAttributeCastError)
                    retic_assert(retic_has_type(getattr(val, m), trg.members[m]), val, msg)
            return retic_monotonic_cast(val, src, trg, trg.members, msg, line)
        elif retic_tyinstance(trg, typing.Function):
            call = '__new__' if isinstance(val, type) else '__call__'
            if call in src.members:
                nsrc = src.member_type(call).bind()
            else:
                retic_assert(hasattr(val, call), val, msg, exc=ObjectTypeAttributeCastError)
                nsrc = Function(DynParameters, Dyn)
            val = retic_monotonic_cast(val, nsrc, trg, {call: trg}, msg, line)
            return retic_make_function_wrapper(val, nsrc, trg, msg, line)
        else: raise ReticUnimplementedException(src, trg)
    elif retic_tyinstance(src, rtypes.Structural) or retic_tyinstance(trg, Structural):
        #retic_assert(retic_has_type(val, trg), '%s at line %s' % (msg, line))
        #print('lcast')
        return retic_cast(val, src.structure(), trg.structure(), msg, line)
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
    raise CastError(msg)

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
            #retic_warn('Line %d: %s cannot be made monotonic.' % (line, value), 0)
            return False

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
        #print('get', attr)
        if deep_hasattr(obj, '__monotonics__') and attr in getter(obj, '__monotonics__'):
            #print('GETT ', attr, obj.__monotonics__[attr])
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


def retic_dynfunc(ty):
    return rtypes.Function(rtypes.DynParameters, rtypes.Dyn)

def retic_proxy(val, src, join, trg, msg, line, call=None, meta=False):
    Proxy = retic_create_proxy(val)

    typegen = isinstance(val, type) and not meta

    if typegen:
        meta = retic_proxy(val, src, join, trg, msg, line, call=call,meta=True)
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
    Proxy.__cast__ = src, join, trg, msg, line
    Proxy.__getattribute__ = retic_make_getattr(val, src, join, trg, msg, line, function=call)
    Proxy.__setattr__ = retic_make_setattr(val, src, join, trg, msg, line)
    Proxy.__delattr__ = retic_make_delattr(val, src, join, trg, msg, line)
    if not meta:
        return Proxy()
    else:
        return Proxy

def retic_check_threesome(val, src, trg, msg, line):
    #print(src, trg, 't')
    if hasattr(val, '__actual__'):
        nsrc, tm, _, tmsg, tline = val.__cast__
        join = n_info_join(tm, src, trg)
        actual = val.__actual__
    else: 
        actual = val
        join = info_join(src, trg)
        nsrc = src
    retic_assert(join.top_free(), val, msg)
    return actual, nsrc, join 

def retic_get_actual(val):
    if hasattr(val, '__actual__'):
        return val.__actual__
    else: return val

def retic_make_function_wrapper(val, src, trg, msg, line):
    #print(val, src, trg, 'wq')
    base_val, base_src, join = retic_check_threesome(val, src, trg, msg, line)

    src_fmls = src.froms
    src_ret = src.to
    trg_fmls = trg.froms
    trg_ret = trg.to

    fml_len = max(src_fmls.len(), trg_fmls.len())
    bi = inspect.isbuiltin(base_val) or (hasattr(base_val, '__self__') and not hasattr(base_val, '__func__'))

    def wrapper(self, *args, **kwds):
        #print('WC!', *args)
        kwc = len(args)
        ckwds = {}
        if retic_pinstance(src_fmls, rtypes.NamedParameters):
            for k in kwds:
                if k in [k for k, _ in src_fmls.parameters]:
                    kwc -= 1
                    ckwds[k] = retic_cast(kwds[k], rtypes.Dyn, dict(src_fmls.parameters)[k], msg, line=line)
                else: ckwds[k] = kwds[k]
        if fml_len != -1:
            retic_assert(len(args)+len(kwds) == fml_len, val, msg)
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

    return retic_proxy(base_val, base_src, join, trg, msg, line, call=wrapper)

def retic_make_proxy(val, src, trg, msg, line, ext_join=None):
    #print(src, trg, 'mp')
    val, src, join = retic_check_threesome(val, src, trg, msg, line)
    if isinstance(val, type):
        def construct(cls, *args, **kwd):
            c = val.__new__(val)
            prox = retic_make_proxy(c, src.instance(), trg.instance(), msg, line, join.instance())
            prox.__init__(*args, **kwd)
            return prox
    else:
        construct = None

    return retic_proxy(val, src, join, trg, msg, line, call=construct)
    
def retic_mergecast(val, src, trg, msg, line):
    return retic_cast(val, src, retic_merge(src, trg), msg, line)

def retic_make_getattr(obj, src, join, trg, msg, line, function=None):
    def n_getattr(prox, attr):
        if attr == '__cast__':
            return (src, join, trg, msg, line)
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
        ljoin = join.member_type(attr, rtypes.Dyn)
        ltrg = trg.member_type(attr, rtypes.Dyn)
        return retic_mergecast(retic_mergecast(val, lsrc, ljoin, msg, line=line), ljoin, ltrg, msg, line=line)
    return n_getattr

def retic_make_setattr(obj, src, join, trg, msg, line):
    def n_setattr(prox, attr, val):
        lsrc = src.member_type(attr, rtypes.Dyn)
        ljoin = join.member_type(attr, rtypes.Dyn)
        ltrg = trg.member_type(attr, rtypes.Dyn)
        setattr(obj, attr, retic_mergecast(retic_mergecast(val, ltrg, ljoin, msg, line),
                                           ljoin, lsrc, msg, line))
    return n_setattr

def retic_make_delattr(obj, src, join, trg, msg, line):
    def n_delattr(prox, attr):
        ljoin = join.member_type(attr, rtypes.Dyn)
        if retic_tyinstance(ljoin, rtypes.Dyn):
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

def retic_getitem_static(val, item, ty):
    if retic_monotonic_installed(val):
        return val.__fastgetitem__(item)
    else: return retic_check(val[item], ty, 'Item in non-object value ill-typed', line=inspect.currentframe().f_back.f_lineno)

def retic_getitem_dynamic(val, item, ty):
    if retic_monotonic_installed(val):
        return val.__getitem_attype__(item, ty)
    else: return retic_check(val[item], ty, 'Item in non-object value ill-typed', line=inspect.currentframe().f_back.f_lineno)        

def retic_setitem_static(val, item, written, ty):
    if retic_monotonic_installed(val):
        val.__fastsetitem__(item, written)
    else: # If val is not a monotonic object, fall back to casts-as-check
        retic_check(written, ty, 'Item in non-object value ill-typed', line=inspect.currentframe().f_back.f_lineno)
        val[item] = written

def retic_setitem_dynamic(val, item, written, ty):
    if retic_monotonic_installed(val):
        val.__setitem_attype__(item, written, ty)
    else: 
        retic_check(written, ty, 'Item in non-object value ill-typed', line=inspect.currentframe().f_back.f_lineno)
        val[item] = written


def retic_actual(v):
    return v


def retic_bindmethod_static(cls, receiver, attr, ty):
    val = retic_getattr_static(receiver, attr, ty)
    if inspect.ismethod(val):
        return lambda *args: retic_getattr_static(cls, attr, ty)(receiver, *args)
    else: return val

def retic_bindmethod_dynamic(cls, receiver, attr, ty):
    val = retic_getattr_dynamic(receiver, attr, ty)
    if inspect.ismethod(val):
        return lambda *args: retic_getattr_dynamic(cls, attr, ty)(receiver, *args)
    else: return val
