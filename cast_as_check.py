from typing import has_type as retic_has_type
import inspect

# Casts 
# Cast-as-check
def retic_cast(val, src, trg, msg):
    # Can't (easily) just call retic_cas_check because of frame introspection resulting in
    # incorrect line number reporting
    assert retic_has_type(val, trg), "%s at line %d (expected %s)" % (msg, inspect.currentframe().f_back.f_lineno, trg)
    return val

def retic_check(val, trg, msg):
    assert retic_has_type(val, trg), "%s at line %d" % (msg, inspect.currentframe().f_back.f_lineno)
    return val

def retic_error(msg):
    assert False, "%s at line %d" % (msg, inspect.currentframe().f_back.f_lineno)

