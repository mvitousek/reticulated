from typing import has_type as retic_has_type
from relations import tymeet as retic_tymeet, Bot as ReticBot
import typing
from exc import UnimplementedException as ReticReticUnimplementedException
import inspect

class ReticBox(object):
    def __init__(self, value, ty):
        self.value = value
        self.ty = ty
        
    def unbox(self):
        return self.value

    def type(self):
        return self.ty

    def __str__(self):
        return '<%s boxed from %s>' % (self.value,  self.ty)

class InternalTypeError(Exception):
    pass

def retic_strengthen_monotonics(value, new, line):
    new = new.copy()
    if not hasattr(value, '__monotonics__'):
        value.__monotonics__ = new
    else:
        for attr in new:
            if attr in value.__monotonics__:
                try:
                    value.__monotonics__ = retic_tymeet([new[attr], 
                                                         value.__monotonics__[attr]])
                except ReticBot:
                    assert False, "References with incompatible types referring to same object at line %d" % (msg, line)
            else:
                value.__monotonics__[attr] = new[attr]

def retic_setup_type(value, ty, line):
    if type(ty) == typing.Object:
        for mem in ty.members:
            try:
                mem_val = getattr(value, mem)
                setattr(value, mem, None) # If this is a read-only value, find out before casting stuff
                new_mem_val = retic_cast(mem_val, typing.Dyn, ty.members[mem], 'Cast failure', line=line)
                setattr(value, mem, new_mem_val)
            except AttributeError:
                raise InternalTypeError
        retic_strengthen_monotonics(value, ty.members, line=line)

        if not retic_has_type(value, ty): #Check objects here: later and the accessor will upcast things to *
            raise InternalTypeError
        
        if not hasattr(value.__class__, '__fastsetattr__'):
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

            deleter = value.__class__.__delattr__
            def new_deleter(obj, attr):
                if hasattr(obj, '__monotonics__') and attr in obj.__monotonics__:
                    assert False, "Attempting to delete monotonic attribute at line %d" % line
                else: deleter(obj, attr)
            value.__class__.__delattr__ = new_deleter
        
        if not hasattr(value.__class__, '__fastgetattr__'):
            getter = value.__class__.__getattribute__
            value.__class__.__fastgetattr__ = getter
            def deep_hasattr(obj, attr):
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
    elif not retic_has_type(value, ty):
        raise InternalTypeError

# Casts 
def retic_cast(val, src, trg, msg, line=inspect.currentframe().f_back.f_lineno):
    try:
        if src == trg:
            return val
        elif typing.tyinstance(trg, typing.Dyn):
            return ReticBox(val, src)
        elif typing.tyinstance(src, typing.Dyn):
            if type(val) == ReticBox:
                if type(val.type()) == type(trg):
                    return retic_cast(val.unbox(), val.type(), trg, msg, line=line)
                else:
                    assert False, "%s at line %d" % (msg, line)
            else:
                retic_setup_type(val, trg, line=line)
                return val
        elif type(src) != type(trg):
            assert False, "%s at line %d" % (msg, line)
        elif typing.tyinstance(src, typing.Object) and typing.tyinstance(trg, typing.Object):
            smems = src.members
            tmems = trg.members
            raise ReticUnimplementedException('working on it')
        else: raise ReticUnimplementedException('Unhandled cast')
    except TypeError:
        assert False, "%s at line %d" % (msg, line)

def retic_check(val, trg, msg, line=inspect.currentframe().f_back.f_lineno):
    # This needs to be a NAIVE SUPERTYPE check
    #assert retic_has_type(val, trg), "%s at line %d" % (msg, inspect.currentframe().f_back.f_lineno)
    return val

def retic_error(msg, line=inspect.currentframe().f_back.f_lineno):
    assert False, "%s at line %d" % (msg, line)

def retic_getattr(val, attr, ty, speed):
    if hasattr(val, '__fastgetattr__'):
        if speed == 'slow':
            return val.__getattr_attype__(attr, ty)
        else: return val.__fastgetattr__(attr)
    else: return retic_check(getattr(val, attr), ty, 'Attribute in non-object value ill-typed', line=inspect.currentframe().f_back.f_lineno)
        
def retic_setattr(val, attr, written, ty, speed):
    if hasattr(val, '__fastsetattr__'):
        if speed == 'slow':
            val.__setattr_attype__(attr, written, ty)
        else: 
            val.__fastsetattr__(attr, written)
    else: 
        retic_check(written, ty, 'Attribute in non-object value ill-typed', line=inspect.currentframe().f_back.f_lineno)
        setattr(val, attr, written)
