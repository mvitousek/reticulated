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
    if retic_tyinstance
    assert retic_has_type(val, trg), "%s at line %d (expected %s)" % (msg, inspect.currentframe().f_back.f_lineno, trg)
    return val

def retic_check(val, trg, msg):
    assert retic_has_type(val, trg), "%s at line %d" % (msg, inspect.currentframe().f_back.f_lineno)
    return val

def retic_error(msg):
    assert False, "%s at line %d" % (msg, inspect.currentframe().f_back.f_lineno)

