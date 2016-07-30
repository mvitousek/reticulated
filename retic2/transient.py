## Runtime module used by Transient

class RuntimeCheckError(Exception): pass

def __retic_check(val, ty):
    if ty is callable:
        if callable(val):
            return val
        else: raise RuntimeCheckError()
    elif ty is None:
        if val is None:
            return val
        else: raise RuntimeCheckError()
    elif ty is float:
        if not isinstance(val, float):
            return __retic_check(val, int)
        else: 
            return val
    elif isinstance(val, ty):
        return val
    else: raise RuntimeCheckError()

def __retic_check_int(val):
    if isinstance(val, int):
        return val
    raise RuntimeCheckError()

def __retic_check_fun(val):
    if callable(val):
        return val
    raise RuntimeCheckError()
