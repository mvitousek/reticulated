from .runtime import has_type as retic_has_type
from .relations import tyinstance as retic_tyinstance
from . import rtypes
import inspect

class CastError(Exception):
    pass
class FunctionCastTypeError(CastError, TypeError):
    pass
class ObjectTypeAttributeCastError(CastError, AttributeError):
    pass
class CheckError(Exception):
    pass
class FunctionCheckTypeError(CastError, TypeError):
    pass
class ObjectTypeAttributeCheckError(CastError, AttributeError):
    pass


def retic_assert(bool, val, msg, exc=None):
    if not bool:
        if exc == None:
            exc = CastError
        raise exc(msg % ('\'%s\'' % str(val)))
# Casts 
# Cast-as-check
def retic_cast(val, src, trg, msg):
    if retic_tyinstance(trg, rtypes.Object):
        exc = ObjectTypeAttributeCastError
    elif retic_tyinstance(trg, rtypes.Function) and retic_tyinstance(src, rtypes.Dyn):
        exc = FunctionCastTypeError
    else: exc = CastError
    retic_assert(retic_has_type(val, trg), val, msg, exc)
    return val

def retic_check(val, trg, msg):
    if retic_tyinstance(trg, rtypes.Object):
        exc = ObjectTypeAttributeCheckError
    elif retic_tyinstance(trg, rtypes.Function):
        exc = FunctionCheckTypeError
    else: exc = CheckError
    retic_assert(retic_has_type(val, trg), val, msg, exc)
    return val

def retic_error(msg):
    raise CastError(msg)

def retic_actual(v):
    return v
