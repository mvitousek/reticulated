import vis, type_helpers
from ast import *

class Typeparser(Vistor):
    def parse_type(self, n):
        try:
            ret = self.preorder(n)
            if isinstance(ret, dict):
                return Object(members=ret)
            return self.preorder(n)
        except AttributeError:
            raise UnknownTypeError('Unknown type or part of type in annotation')

    def visitCall(self, n):
        if isinstance(n.func, Name):
            if n.func.id in ['Dyn', 'Int', 'Float', 'Bool', 'Complex', 'String', 
                             'Unicode', 'List', 'Dict', 'Tuple', 'Class', 'Instance', 
                             'Object']:
                return eval(n.func.id)(map(self.dispatch, n.args))
            else: 
                raise UnknownTypeError('Unknown type constructor ', n.func.id)

    def visitDict(self, n):
        d = {}
        for (k, v) in zip(n.keys, n.values):
            if isinstance(k.id, str):
                d[k.id] = self.dispatch(v)
            else: 
                raise UnknownTypeError('Structural object constructor ', k.id, ' not a string')
        return d

    def visitName(self, n):
        if n.id in ['Dyn', 'Int', 'Float', 'Bool', 'Complex', 'String', 
                    'Unicode']:
            return eval(n.id)
        else: 
            return Instance(n.id)

