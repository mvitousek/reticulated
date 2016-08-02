## Runtime module used by Transient

class RuntimeCheckError(BaseException): 
    def __init__(self, *args):
        import sys
        # Deactivate the import hook, so we don't try to typecheck the
        # modules imported by the error handling process
        if hasattr(sys.path_hooks[0], 'retic'):
            sys.path_hooks[0].enabled = False
            sys.path_importer_cache.clear()

def __retic_error(msg):
    # Home of EXTREME EVIL MAGIC
    try:
        raise RuntimeCheckError(msg)
    except RuntimeCheckError as e:
        import ctypes, sys
        tb = e.__traceback__
        
        # Grab the frame from 2 callers ago
        f = sys._getframe(2)
        
        # Cast the traceback object to a pointer type (!!)
        p4 = ctypes.cast(id(tb), ctypes.POINTER(ctypes.c_uint))
        p8 = ctypes.cast(id(tb), ctypes.POINTER(ctypes.c_ulong))
        # Write the call site's frame info into the traceback (!!!)
        p4[8], p4[9] = tb.tb_frame.f_back.f_back.f_lasti, tb.tb_frame.f_back.f_back.f_lineno
        p8[3] = id(tb.tb_frame.f_back.f_back)
        raise

def __retic_check(val, ty):
    if ty is callable:
        if callable(val):
            return val
        else: __retic_error('')
    elif ty is None:
        if val is None:
            return val
        else: raise __retic_error('')
    elif ty is float:
        if not isinstance(val, float):
            return __retic_check(val, int)
        else: 
            return val
    elif isinstance(val, ty):
        return val
    else: raise __retic_error('')

def __retic_check_int(val):
    if isinstance(val, int):
        return val
    raise RuntimeCheckError()

def __retic_check_fun(val):
    if callable(val):
        return val
    raise RuntimeCheckError()
