import inspect, ast, collections, sys
from . import flags, relations
from .exc import UnknownTypeError, UnexpectedTypeError
from .rtypes import *

UNCALLABLES = [Void, Int, Bytes, Float, Complex, String, Bool, Dict, List, Tuple, Set]

class Var(object):
    def __init__(self, var, location=None):
        if location:
            self.location=location
        self.var = var
    def __eq__(self, other):
        return isinstance(other, Var) and \
            other.var == self.var
    def __hash__(self):
        return hash(self.var) + 1
    def __str__(self):
        return 'Var(%s)' % self.var
    __repr__ = __str__

class StarImport(object):
    def __init__(self, var):
        self.var = var
    def __eq__(self, other):
        return isinstance(other, StarImport) and \
            other.var == self.var
    def __hash__(self):
        return hash(self.var) + 2
    def __str__(self):
        return 'StarImport(%s)' % self.var
    __repr__ = __str__


class Misc(object):
    default = dict(ret = Void, cls = None,
                   receiver = None, methodscope = False,
                   extenv = {}, filename = None, depth = 0,
                   static = None)
    def __init__(self, *, extend=None, **kwargs):
        if extend is None:
            class Dummy: pass
            extend = Dummy()
            extend.__dict__.update(self.default)
        self.ret = kwargs.get('ret', extend.ret)
        self.cls = kwargs.get('cls', extend.cls)
        self.receiver = kwargs.get('receiver', extend.receiver)
        self.methodscope = kwargs.get('methodscope', extend.methodscope)
        self.extenv = kwargs.get('extenv', extend.extenv)
        self.filename = kwargs.get('filename', extend.filename)
        self.depth = kwargs.get('depth', extend.depth)
        self.static = kwargs.get('static', extend.static)

# Utilities

def initial_environment():
    if flags.INITIAL_ENVIRONMENT:
        return {
            Var('bool'): Function(DynParameters,Bool),
            Var('int'): Function(DynParameters,Int),
            Var('bytes'): Function(DynParameters,Bytes),
            Var('str'): Function(DynParameters,String),
            Var('float'): Function(DynParameters,Float),
            Var('complex'): Function(DynParameters,Complex),
            Var('dict'): Function(DynParameters,Dict(Dyn, Dyn)),
            Var('list'): Function(DynParameters,List(Dyn)),
            Var('set'): Function(DynParameters,Set(Dyn)),
            Var('len'): Function(DynParameters,Int),
            Var('dyn'): Function(DynParameters,Dyn),
            }
    else: return {}
