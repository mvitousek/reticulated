from typing import has_type as retic_has_type
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

def retic_setup_type(value, ty):
    if type(ty) == typing.Object:
        for mem in ty.members:
            try:
                mem_val = getattr(value, mem)
                setattr(value, mem, None) # If this is a read-only value, find out before casting stuff
                new_mem_val = retic_cast(mem_val, typing.Dyn, ty.members[mem], 'Cast failure')
                setattr(value, mem, new_mem_val)
            except AttributeError:
                raise InternalTypeError
        value.__monotonics__ = ty.members.copy()

        if not retic_has_type(value, ty): #Check objects here: later and the accessor will upcast things to *
            raise InternalTypeError
        
        if not hasattr(value.__class__, '__fastsetattr__'):
            setter = value.__class__.__setattr__
            value.__class__.__fastsetattr__ = setter
            def new_setter(obj, attr, val):
                if hasattr(obj, '__monotonics__') and attr in obj.__monotonics__:
                    val = retic_cast(val, typing.Dyn, obj.__monotonics__[attr], 'Cast failure')
                setter(obj, attr, val)
            value.__class__.__setattr__ = new_setter
            def typed_setter(obj, attr, val, ty):
                if hasattr(obj, '__monotonics__') and attr in obj.__monotonics__:
                    val = retic_cast(val, ty, obj.__monotonics__[attr], 'Cast failure')
                    setter(obj, attr, val)
                else: raise UnexpectedTypeError('Typed-setting an inappropriate value')
            value.__class__.__setattr_attype__ = typed_setter
        
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
                    return retic_cast(getter(obj, attr), getter(obj, '__monotonics__')[attr], typing.Dyn, 'Cast failure')
                else: return getter(obj, attr)
            value.__class__.__getattribute__ = new_getter
            def typed_getter(obj, attr, ty):
                if deep_hasattr(obj, '__monotonics__') and attr in getter(obj, '__monotonics__'):
                    return retic_cast(getter(obj, attr), getter(obj, '__monotonics__')[attr], ty, 'Cast failure')
                elif attr in ['__getattribute__', '__getattr_attype__', '__fastgetattr__', '__setattr__', '__setattr_attype__', '__fastsetattr__']:
                    return getter(obj, attr)
                else: raise UnexpectedTypeError('Typed-getting an inappropriate value')
            value.__class__.__getattr_attype__ = typed_getter
    elif not retic_has_type(value, ty):
        raise InternalTypeError

# Casts 
def retic_cast(val, src, trg, msg):
    try:
        if src == trg:
            return val
        elif typing.tyinstance(trg, typing.Dyn):
            return ReticBox(val, src)
        elif typing.tyinstance(src, typing.Dyn):
            if type(val) == ReticBox:
                if type(val.type()) == type(trg):
                    return retic_cast(val.unbox(), val.type(), trg, msg)
                else:
                    assert False, "%s at line %d" % (msg, inspect.currentFrame().f_back.f_lineno)
            else:
                retic_setup_type(val, trg)
                return val
        elif type(src) != type(trg):
            assert False, "%s at line %d" % (msg, inspect.currentFrame().f_back.f_lineno)
        elif typing.tyinstance(src, typing.Object) and typing.tyinstance(trg, typing.Object):
            smems = src.members
            tmems = trg.members
            raise ReticUnimplementedException('working on it')
        else: raise ReticUnimplementedException('Unhandled cast')
    except TypeError:
        assert False, "%s at line %d" % (msg, inspect.currentframe().f_back.f_lineno)

def retic_check(val, trg, msg):
    # This needs to be a NAIVE SUPERTYPE check
    #assert retic_has_type(val, trg), "%s at line %d" % (msg, inspect.currentframe().f_back.f_lineno)
    return val

def retic_error(msg):
    assert False, "%s at line %d" % (msg, inspect.currentframe().f_back.f_lineno)

def retic_getattr(val, attr, ty, speed):
    if hasattr(val, '__fastgetattr__'):
        if speed == 'slow':
            return val.__getattr_attype__(attr, ty)
        else: return val.__fastgetattr__(attr)
    else: return retic_check(getattr(val, attr), ty, 'Attribute in non-object value ill-typed')
        
def retic_setattr(val, attr, written, ty, speed):
    if hasattr(val, '__fastsetattr__'):
        if speed == 'slow':
            val.__setattr_attype__(attr, written, ty)
        else: 
            val.__fastsetattr__(attr, written)
    else: 
        retic_check(written, ty, 'Attribute in non-object value ill-typed')
        setattr(val, attr, written)
