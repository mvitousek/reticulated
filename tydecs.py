import inspect
from decorator import decorator
from typing import *

# Function decorator -- apply to a function to enable in/out typechecking
@decorator
def typed(fn, *args):
    argspec = inspect.getfullargspec(fn)
    for i in range(len(argspec.args)):
        p = argspec.args[i]
        if p in argspec.annotations:
            assert(has_type(args[i], argspec.annotations[p]))
    ret = fn(*args)
    if 'return' in argspec.annotations:
        assert has_type(ret, argspec.annotations['return']), 'Invalid return value'
    return ret

# Metaclass -- use as a metaclass to enable in/out typechecking on fields
class Typed(type):
    def __init__(cls, *args):
        for name, m in inspect.getmembers(cls, inspect.isfunction):
            setattr(cls, name, typed(m))

# Class -- inherit from to enable in/out typechecking on fields
class TypedObject(object, metaclass=Typed):
    pass

# Class decorator -- apply to a class to enable in/out typechecking on fields
def typed_class(cls):
    for name, m in inspect.getmembers(cls, inspect.isfunction):
        setattr(cls, name, typed(m))
    return cls
