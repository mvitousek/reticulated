from opt_transient import *

## Runtime module used by Transient

__all__ = ['__retic_check_int__', '__retic_check_float__', '__retic_check_list__', '__retic_check_set__', '__retic_check_dict__', '__retic_check_instance__', '__retic_check_class__', '__retic_check_structural__', '__retic_check_none__', '__retic_check_callable__', '__retic_check_str__', '__retic_check_bool__', '__retic_check_tuple__', '__retic_check_htuple__']


def __retic_cast_callable__(val, src, trg, line, col):
    add_cast(val, src, trg, line, col)
    return val if callable(val) else error('Value {} is not a function'.format(val))

def __retic_cast_instance__(val, src, trg, line, col, ty):
    add_cast(val, src, trg, line, col)
    return val if isinstance(val, ty) else error('Value {} is not an instance of type {}'.format(val, ty))

def __retic_cast_tuple__(val, src, trg, line, col, n):
    add_cast(val, src, trg, line, col)
    return val if isinstance(val, tuple) and len(val) == n else error('Value {} is not a {}-tuple'.format(val, n))

def __retic_cast_htuple__(val, src, trg, line, col):
    add_cast(val, src, trg, line, col)
    return val if isinstance(val, tuple) else error('Value {} is not a tuple'.format(val))

def __retic_cast_module__(val, src, trg, line, col):
    add_cast(val, src, trg, line, col)
    from types import ModuleType
    return val if isinstance(val, ModuleType) else error('Value {} is not a module'.format(val))

def __retic_cast_class__(val, src, trg, line, col, ty):
    add_cast(val, src, trg, line, col)
    return val if ty in getattr(val, 'mro', lambda: [])() else error('Value {} is not a subtype of {}'.format(val, ty))

def __retic_cast_union__(val, src, trg, line, col, alts):
    add_cast(val, src, trg, line, col)
    # We can optimize this by having the compiler provide a list of check functions to apply to val.
    from . import transient
    return transient.__retic_cast__(val, transient.__retic_union__(alts))

def __retic_cast_structural__(val, src, trg, line, col, ty):
    add_cast(val, src, trg, line, col)
    mk = ''
    try:
        for k in ty:
            mk = k
            getattr(val, k)
        return val
    except:
        error('Value {} does not have member {}'.format(val, mk))

def __retic_cast_list__(val, src, trg, line, col):
    add_cast(val, src, trg, line, col)
    return val if isinstance(val, list) else error('Value {} is not a list'.format(val))

def __retic_cast_set__(val, src, trg, line, col):
    add_cast(val, src, trg, line, col)
    return val if isinstance(val, set) else error('Value {} is not a set'.format(val))

def __retic_cast_dict__(val, src, trg, line, col):
    add_cast(val, src, trg, line, col)
    return val if isinstance(val, dict) else error('Value {} is not a dictionary'.format(val))

def add_cast(val, src, trg, line, col):
    pt = line << 32 + col
    if hasattr(val, '__retic_casts__'):
        if pt not in val.__retic_casts__:
            val.__retic_casts__[pt] = (src, trg)
    else:
        try:
            val.__retic_casts__ = { pt: (src, trg) }
            val.__retic_pointers__ = {}
        except AttributeError:
            pass

def __retic_blame_check_int__(val, resp, tag):
    return val if isinstance(val, int) else blame(val, resp, tag, 'Value {} is not an integer'.format(val))

def __retic_blame_check_bool__(val, resp, tag):
    return val if isinstance(val, bool) else blame(val, resp, tag, 'Value {} is not a boolean'.format(val))

def __retic_blame_check_str__(val, resp, tag):
    return val if isinstance(val, str) else blame(val, resp, tag, 'Value {} is not a string'.format(val))

def __retic_blame_check_callable__(val, resp, tag):
    if hasattr(val, '__retic_pointers__'): 
        if resp not in val.__retic_pointers__:
            val.__retic_pointers__[resp] = tag
    else:
        try:
            val.__retic_pointers__ = { resp: tag }
        except AttributeError:
            pass
    return val if callable(val) else blame(val, resp, tag, 'Value {} is not a function'.format(val))

def __retic_blame_check_float__(val, resp, tag):
    return val if isinstance(val, float) else (val if isinstance(val, int) else blame(val, resp, tag, 'Value {} is not a function'.format(val)))

def __retic_blame_check_none__(val, resp, tag):
    return None if val is None else blame(val, resp, tag, 'Value {} is not None'.format(val))

def __retic_blame_check_instance__(val, resp, tag, ty):
    if hasattr(val, '__retic_pointers__'): 
        if resp not in val.__retic_pointers__:
            val.__retic_pointers__[resp] = tag
    else:
        try:
            val.__retic_pointers__ = { resp: tag }
        except AttributeError:
            pass
    return val if isinstance(val, ty) else blame(val, resp, tag, 'Value {} is not an instance of type {}'.format(val, ty))

def __retic_blame_check_tuple__(val, resp, tag, n):
    if hasattr(val, '__retic_pointers__'): 
        if resp not in val.__retic_pointers__:
            val.__retic_pointers__[resp] = tag
    else:
        try:
            val.__retic_pointers__ = { resp: tag }
        except AttributeError:
            pass
    return val if isinstance(val, tuple) and len(val) == n else blame(val, resp, tag, 'Value {} is not a {}-tuple'.format(val, n))

def __retic_blame_check_htuple__(val, resp, tag):
    if hasattr(val, '__retic_pointers__'): 
        if resp not in val.__retic_pointers__:
            val.__retic_pointers__[resp] = tag
    else:
        try:
            val.__retic_pointers__ = { resp: tag }
        except AttributeError:
            pass
    return val if isinstance(val, tuple) else blame(val, resp, tag, 'Value {} is not a tuple'.format(val))

def __retic_blame_check_module__(val, resp, tag):
    if hasattr(val, '__retic_pointers__'): 
        if resp not in val.__retic_pointers__:
            val.__retic_pointers__[resp] = tag
    else:
        try:
            val.__retic_pointers__ = { resp: tag }
        except AttributeError:
            pass
    from types import ModuleType
    return val if isinstance(val, ModuleType) else blame(val, resp, tag, 'Value {} is not a module'.format(val))

def __retic_blame_check_class__(val, resp, tag, ty):
    if hasattr(val, '__retic_pointers__'): 
        if resp not in val.__retic_pointers__:
            val.__retic_pointers__[resp] = tag
    else:
        try:
            val.__retic_pointers__ = { resp: tag }
        except AttributeError:
            pass
    return val if ty in getattr(val, 'mro', lambda: [])() else blame(val, resp, tag, 'Value {} is not a subtype of {}'.format(val, ty))

def __retic_blame_check_union__(val, resp, tag, alts):
    if hasattr(val, '__retic_pointers__'): 
        if resp not in val.__retic_pointers__:
            val.__retic_pointers__[resp] = tag
    else:
        try:
            val.__retic_pointers__ = { resp: tag }
        except AttributeError:
            pass
    # We can optimize this by having the compiler provide a list of check functions to apply to val.
    from . import transient
    return transient.__retic_blame_check__(val, transient.__retic_union__(alts))

def __retic_blame_check_structural__(val, resp, tag, ty):
    if hasattr(val, '__retic_pointers__'): 
        if resp not in val.__retic_pointers__:
            val.__retic_pointers__[resp] = tag
    else:
        try:
            val.__retic_pointers__ = { resp: tag }
        except AttributeError:
            pass
    mk = ''
    try:
        for k in ty:
            mk = k
            getattr(val, k)
        return val
    except:
        blame(val, resp, tag, 'Value {} does not have member {}'.format(val, mk))

def __retic_blame_check_list__(val, resp, tag):
    if hasattr(val, '__retic_pointers__'): 
        if resp not in val.__retic_pointers__:
            val.__retic_pointers__[resp] = tag
    else:
        try:
            val.__retic_pointers__ = { resp: tag }
        except AttributeError:
            pass
    return val if isinstance(val, list) else blame(val, resp, tag, 'Value {} is not a list'.format(val))

def __retic_blame_check_set__(val, resp, tag):
    if hasattr(val, '__retic_pointers__'): 
        if resp not in val.__retic_pointers__:
            val.__retic_pointers__[resp] = tag
    else:
        try:
            val.__retic_pointers__ = { resp: tag }
        except AttributeError:
            pass
    return val if isinstance(val, set) else blame(val, resp, tag, 'Value {} is not a set'.format(val))

def __retic_blame_check_dict__(val, resp, tag):
    if hasattr(val, '__retic_pointers__'): 
        if resp not in val.__retic_pointers__:
            val.__retic_pointers__[resp] = tag
    else:
        try:
            val.__retic_pointers__ = { resp: tag }
        except AttributeError:
            pass
    return val if isinstance(val, dict) else blame(val, resp, tag, 'Value {} is not a dictionary'.format(val))

def blame(val, resp, tag, msg):
    candidates = []

def collectblame(rs, val):
    if hasattr(val, '__retic_casts__'):
        candidates = [(pt, extract(rs, val.__retic_casts__[pt])) for pt in val.__retic_casts__]
    else:
        candidates = []
        
    for ref in getattr(val, '__retic_pointers__', []):
        candidates += collectblame([val.__retic_pointers__[ref]] + rs, ref)

    return candidates

def extract(rs, cast):
    import pickle
    src, trg = cast
    return extract_cast(rs, pickle.loads(src), pickle.loads(trg))

def extract_cast(rs, src, trg):


    if len(rs) == 0:
        return (src, trg)
    else:
        tag  = rs[0]
        rs   = rs[1:]
        attr = None
 
        if isinstance(tag, tuple):
            tag, attr = tag
            
        kind = tag & 0b111
        n = tag >> 3
        
        if kind == 4:
            assert attr is not None # getattr
            
        elif kind == 3:
            pass # gettupleitem
        elif kind == 2:
            pass # getitem
        elif kind == 1:
            pass # posarg
        elif kind == 0:
            pass # ret
        else:
            raise exc.InternalReticulatedError()
        
