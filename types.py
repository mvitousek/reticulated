from operator import and_
from functools import reduce

class PyType(object):
    pass
class Dyn(PyType):
    alias = None
class Int(PyType):
    alias = int
class Float(PyType):
    alias = float
class Complex(PyType):
    alias = complex
class String(PyType):
    alias = str
class Unicode(PyType):
    alias = unicode
class Bool(PyType):
    alias = bool
class List(PyType):
    def __init__(self, type):
        self.type = type
class Dict(PyType):
    def __init__(self, keys, values):
        self.keys = keys
        self.values = values
class Tuple(PyType):
    def __init__(self, *elements):
        self.elements = elements
class Class(PyType):
    def __init__(self, members=None, klass=None):
        if members == None and klass == None:
            raise TypeError('A class type must be constructed with either a members or klass argument')
        if members != None and klass != None:
            raise TypeError('A class type must be constructed with only one of a members or a klass argument')
        if members != None:
            self.members = members
        else:
            # Get the members of the class
            pass
class Object(PyType):
    def __init__(self, members=None, obj=None):
        if members == None and obj == None:
            raise TypeError('An object type must be constructed with either a members or obj argument')
        if members != None and obj != None:
            raise TypeError('An object type must be constructed with only one of a members and a obj argument')
        if members != None:
            self.members = members
        else:
            # Get the members of the object
            pass

def tyinstance(ty, tyclass):
    try:
        return isinstance(ty, tyclass) or ty == tyclass or ty == tyclass.alias
    with AttributeError:
        return False
 
def has_type(val, ty):
    if tyinstance(ty, Dyn):
        return True
    elif tyinstance(ty, Int):
        return isinstance(val, int)
    elif tyinstance(ty, Bool):
        return isinstance(val, bool)
    elif tyinstance(ty, Float):
        return isinstance(val, float)
    elif tyinstance(ty, Complex):
        return isinstance(val, complex)
    elif tyinstance(ty, String):
        return isinstance(val, str)
    elif tyinstance(ty, Unicode):
        return isinstance(val, unicode)
    elif tyinstance(ty, List):
        return isinstance(val, list) and \
            reduce(and_, map(lambda x: has_type(x, ty.type), val))
    elif tyinstance(ty, Dict):
        return isinstance(val, dict) and \
            reduce(and_, map(lambda x: has_type(x, ty.keys), val.keys())) and \
            reduce(and_, map(lambda x: has_type(x, ty.values), val.values()))
    elif tyinstance(ty, Tuple):
        return isinstance(val, tuple) and len(ty.elements) == len(val) and \
            reduce(and_, map(lambda p: has_type(p[0], p[1]), zip(val, ty.elements)))
            
