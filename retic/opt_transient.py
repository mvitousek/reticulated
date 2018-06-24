## Runtime module used by Transient

__all__ = ['__retic_check_int__', '__retic_check_float__', '__retic_check_complex__', '__retic_check_list__', '__retic_check_set__', '__retic_check_dict__', '__retic_check_instance__', '__retic_check_class__', '__retic_check_structural__', '__retic_check_none__', '__retic_check_callable__', '__retic_check_str__', '__retic_check_bool__', '__retic_check_tuple__', '__retic_check_htuple__']

ENABLE_EXCEPTHOOK = True

def __retic_error__(msg):
    from . import base_runtime_exception
    class RuntimeCheckError(base_runtime_exception.NormalRuntimeError): pass

    if ENABLE_EXCEPTHOOK:
        import sys
        # Deactivate the import hook, so we don't try to typecheck the
        # modules imported by the error handling process
        if hasattr(sys.path_hooks[0], 'retic') and sys.path_hooks[0].enabled:
            sys.path_hooks[0].enabled = False
            sys.path_importer_cache.clear()

        def excepthook(ty, val, tb):
            from . import exc
            exc.handle_runtime_error(ty, val, tb)

        if sys.excepthook is not excepthook:
            sys.excepthook = excepthook

    raise RuntimeCheckError(msg)

def __retic_check_int__(val):
    return val if isinstance(val, int) else __retic_error__('Value {} is not an integer'.format(val))

def __retic_check_bool__(val):
    return val if isinstance(val, bool) else __retic_error__('Value {} is not a boolean'.format(val))

def __retic_check_str__(val):
    return val if isinstance(val, str) else __retic_error__('Value {} is not a string'.format(val))

def __retic_check_callable__(val):
    return val if callable(val) else __retic_error__('Value {} is not a function'.format(val))

def __retic_check_float__(val):
    return val if isinstance(val, float) else (val if isinstance(val, int) else __retic_error__('Value {} is not a float'.format(val)))

def __retic_check_complex__(val):
    return val if (isinstance(val, complex) or isinstance(val, float) or isinstance(val, int)) else __retic_error__('Value {} is not a complex'.format(val))

def __retic_check_none__(val):
    return None if val is None else __retic_error__('Value {} is not None'.format(val))

def __retic_check_instance__(val, ty):
    return val if isinstance(val, ty) or val is None else __retic_error__('Value {} is not an instance of type {}'.format(val, ty))

def __retic_check_tuple__(val, n):
    return val if isinstance(val, tuple) and len(val) == n else __retic_error__('Value {} is not a {}-tuple'.format(val, n))

def __retic_check_htuple__(val):
    return val if isinstance(val, tuple) else __retic_error__('Value {} is not a tuple'.format(val))

def __retic_check_module__(val):
    from types import ModuleType
    return val if isinstance(val, ModuleType) else __retic_error__('Value {} is not a module'.format(val))

def __retic_check_class__(val, ty):
    return val if ty in getattr(val, 'mro', lambda: [])() else __retic_error__('Value {} is not a subtype of {}'.format(val, ty))

def __retic_check_union__(val, alts):
    # We can optimize this by having the compiler provide a list of check functions to apply to val.
    from . import transient
    return transient.__retic_check__(val, transient.__retic_union__(alts))

def __retic_check_structural__(val, ty):
    mk = ''
    try:
        for k in ty:
            mk = k
            getattr(val, k)
        return val
    except:
        __retic_error__('Value {} does not have member {}'.format(val, mk))

def __retic_check_list__(val):
    return val if isinstance(val, list) else __retic_error__('Value {} is not a list'.format(val))

def __retic_check_set__(val):
    return val if isinstance(val, set) or isinstance(val, frozenset) else __retic_error__('Value {} is not a set'.format(val))

def __retic_check_dict__(val):
    return val if isinstance(val, dict) else __retic_error__('Value {} is not a dictionary'.format(val))
