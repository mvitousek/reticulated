## Runtime module used by Transient

__all__ = ['__retic_check__', '__retic_type_marker__']

from . import base_runtime_exception

class RuntimeCheckError(base_runtime_exception.NormalRuntimeError): pass

ENABLE_EXCEPTHOOK = True

def error(msg, error_on_fail):
    if error_on_fail and ENABLE_EXCEPTHOOK:
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

class __retic_type_marker__:
    def __init__(self, ty):
        self.ty = ty

class __retic_union__:
    def __init__(self, alternatives):
        self.alternatives = alternatives

def __retic_check__(val, ty, error_on_fail=True):
    if ty is callable:
        if callable(val):
            return val
        else: error('Value "{}" is not callable'.format(val), error_on_fail)
    elif ty is None:
        if val is None:
            return val
        else: raise error('Value "{}" is not None'.format(val), error_on_fail)
    elif ty is float:
        if not isinstance(val, float):
            return __retic_check__(val, int)
        else: 
            return val
    elif isinstance(ty, __retic_union__):
        for alt in ty.alternatives:
            try:
                __retic_check__(val, alt, error_on_fail=False)
                return val
            except:
                pass
        error('Value "{}" does not have any of the following types: {}'.format(val, ty.alternatives), error_on_fail)
    elif isinstance(ty, __retic_type_marker__):
        if val is ty.ty:
            return val
        else: error('Value "{}" does not have type {}'.format(val, ty.__name__))
    elif isinstance(ty, list):
        for k in ty:
            if not hasattr(val, k):
                error('Value "{}" does not have attribute "{}"'.format(val, k))
        return val
    elif isinstance(val, ty):
        return val
    else: error('Value "{}" does not have type {}'.format(val, ty.__name__), error_on_fail)
