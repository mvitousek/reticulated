from typing import has_type as retic_has_type, warn as retic_warn
from relations import tymeet as retic_tymeet, Bot as ReticBot
from exc import UnimplementedException as ReticUnimplementedException
import typing, inspect


def retic_actual(v):
    if hasattr(v, '__actual__'):
        return v.__actual__
    return v

class InternalTypeError(Exception):
    pass

def retic_read_only_attribute(value, mem):
    current = getattr(value, mem)
    try:
        setattr(value, mem, current)
        return True
    except AttributeError:
        return False

def retic_make_function_wrapper(fun, src_fmls, trg_fmls, src_ret, trg_ret, line):
    assert len(src_fmls) == len(trg_fmls)
    def wrapper(*args):
        assert len(args) == len(trg_fmls), 'Incorrect number of arguments to function at line %d' % line
        cargs = [ retic_cast(arg, trg, src, 'Parameter of incorrect type', line=line) for arg, trg, src in zip(args, trg_fmls, src_fmls) ]
        ret = fun(*cargs)
        return retic_cast(ret, src_ret, trg_ret)
    wrapper.__name__ = fun.__name__
    return wrapper

def retic_strengthen_monotonics(value, new, line):
    new = new.copy()
    if not hasattr(value, '__monotonics__'):
        value.__monotonics__ = new
    else:
        for attr in new:
            if attr in value.__monotonics__:
                try:
                    value.__monotonics__[attr] = retic_tymeet([new[attr], 
                                                               value.__monotonics__[attr]])
                except ReticBot:
                    assert False, "References with incompatible types referring to same object at line %d" % (msg, line)
            else:
                value.__monotonics__[attr] = new[attr]

def retic_setup_type(value, ty, line):
    if type(ty) == typing.Record:
        retic_monotonic_cast(value, ty.members, line)
    elif not retic_has_type(value, ty):
        raise InternalTypeError('value %s does not have type %s' % (value, ty))


def retic_monotonic_cast(value, members, line):
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
                trgty = retic_tymeet([srcty, upd[mem]])
                new_mem_val = retic_cast(mem_val, srcty, trgty, 'Cast failure', line=line)
                setattr(location, mem, new_mem_val)
            except ReticBot:
                raise InternalTypeError
            except AttributeError:
                retic_warn('Unable to modify %s attribute of value %s at line %d' % (mem, location, line), 0)
                continue
        retic_strengthen_monotonics(location, monotonics, line=line)
        
        if retic_can_be_monotonic(location, line) and not retic_monotonic_installed(location.__class__):
            retic_install_setter(location, line)
            retic_install_deleter(location, line)
            retic_install_getter(location, line)

# Casts 
def retic_cast(val, src, trg, msg, line=None):
    if line == None:
        line = inspect.currentframe().f_back.f_lineno
    try:
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

def retic_check(val, trg, msg, line=inspect.currentframe().f_back.f_lineno):
    # This needs to be a NAIVE SUPERTYPE check, MAYBE?
    #assert retic_has_type(val, trg), "%s at line %d" % (msg, inspect.currentframe().f_back.f_lineno)
    return val

def retic_error(msg, line=inspect.currentframe().f_back.f_lineno):
    assert False, "%s at line %d" % (msg, line)

def retic_monotonic_installed(value):
    return hasattr(value, '__fastsetattr__')

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
