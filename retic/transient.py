## Runtime module used by Transient

__all__ = ['__retic_check__', '__retic_type_marker__']

from . import base_runtime_exception

class RuntimeCheckError(base_runtime_exception.NormalRuntimeError): pass

def error(msg):
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

def __retic_check__(val, ty):
    if ty is callable:
        if callable(val):
            return val
        else: error('Value "{}" is not callable'.format(val))
    elif ty is None:
        if val is None:
            return val
        else: raise error('Value "{}" is not None'.format(val))
    elif ty is float:
        if not isinstance(val, float):
            return __retic_check__(val, int)
        else: 
            return val
    elif isinstance(ty, __retic_type_marker__):
        return val is ty.ty
    elif isinstance(val, ty):
        return val
    else: raise error('Value "{}" does not have type {}'.format(val, ty.__name__))
