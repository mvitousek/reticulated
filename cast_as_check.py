from typing import has_type as retic_has_type
from relations import tyinstance as retic_tyinstance
import rtypes
import inspect

class CastError(Exception):
    pass
class FunctionCastTypeError(CastError, TypeError):
    pass
class ClassTypeAttributeError(CastError, AttributeError):
    pass

def retic_assert(bool, msg, exc=None):
    if not bool:
        if exc == None:
            exc = CastError
        raise exc(msg)

# Casts 
# Cast-as-check
def retic_cast(val, src, trg, msg):
    if retic_tyinstance(trg, rtypes.Object):
        exc = ClassTypeAttributeError
    elif retic_tyinstance(trg, rtypes.Function) and retic_tyinstance(src, rtypes.Dyn):
        exc = FunctionCastTypeError
    else: exc = CastError
    retic_assert(retic_has_type(val, trg), "%s at line %d (expected %s)" % (msg, inspect.currentframe().f_back.f_lineno, trg), exc)
    return val

def retic_check(val, trg, msg):
    if retic_tyinstance(trg, rtypes.Object):
        exc = ClassTypeAttributeError
    elif retic_tyinstance(trg, rtypes.Function):
        exc = FunctionCastTypeError
    else: exc = CastError
    retic_assert(retic_has_type(val, trg), "%s at line %d" % (msg, inspect.currentframe().f_back.f_lineno), exc)
    return val

def retic_error(msg):
    retic_assert(False, "%s at line %d" % (msg, inspect.currentframe().f_back.f_lineno))

