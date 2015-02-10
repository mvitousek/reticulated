import ast, typing, flags
from vis import Visitor
from visitors import DictGatheringVisitor
from typing import *
from relations import *
from exc import StaticTypeError
from errors import errmsg

def update(add, defs, constants={}, location=None, file=None):
    for x in add:
        if x not in constants:
            if x not in defs:
                defs[x] = add[x]
            else:
                defs[x] = tyjoin([add[x], defs[x]])
        elif flags.FINAL_PARAMETERS:
            if not subcompat(add[x], constants[x]):
                raise StaticTypeError(errmsg('BAD_DEFINITION', file, location, x, constants[x], add[x]))
        elif x not in defs:
            defs[x] = tyjoin([add[x], constants[x]])
        else:
            defs[x] = tyjoin([add[x], constants[x], defs[x]])

class Inferfinder(DictGatheringVisitor):
    examine_functions = False
    filename = 'dummy'

    def __init__(self, inference):
        super().__init__()
        self.vartype = InferBottom if inference else Dyn

    def combine_expr(self, s1, s2):
        s2.update(s1)
        return s2

    def combine_stmt(self, s1, s2):
        if flags.JOIN_BRANCHES:
            update(s1, s2, location=s1, file=self.filename)
        else: 
            s2 = {k:s2[k] if k in s1 else Dyn for k in s2}
            s1 = {k:s1[k] if k in s2 else Dyn for k in s1}
            update(s1,s2, location=s1, file=self.filename)
        return s2

    def combine_stmt_expr(self, stmt, expr):
        update(stmt, expr, location=stmt, file=self.filename)
        return expr
    
    def default_expr(self, n):
        return {}
    def default_stmt(self, *k):
        return {}

    def visitClassDef(self, n):
        return {}
        
    def visitName(self, n):
        if isinstance(n.ctx, ast.Store):
            return {Var(n.id): self.vartype}
        else: return {}

    def visitTuple(self, n):
        env = {}
        if isinstance(n.ctx, ast.Store):
            [env.update(self.dispatch(t)) for t in n.elts]
        return env

    def visitList(self, n):
        if isinstance(n.ctx, ast.Store):
            return self.visitTuple(n)
        else: return {}
