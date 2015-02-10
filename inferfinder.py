import ast, typing, flags
from vis import Visitor
from visitors import DictGatheringVisitor, GatheringVisitor, SetGatheringVisitor
from typing import *
from relations import *
from exc import StaticTypeError
from errors import errmsg
from gatherers import Classfinder, Killfinder, Aliasfinder, Inheritfinder, ClassDynamizationVisitor
from importer import ImportFinder

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

    def visitAssign(self, n):
        vty = self.vartype
        env = {}
        for t in n.targets:
            env.update(self.dispatch(t, vty))
        return env

    def visitAugAssign(self, n, *args):
        vty = self.vartype
        return self.dispatch(n.target, vty)

    def visitFor(self, n):
        vty = self.vartype
        env = self.dispatch(n.target, vty)

        body = self.dispatch_statements(n.body)
        orelse = self.dispatch_statements(n.orelse) if n.orelse else self.empty_stmt()
        uenv = self.combine_stmt(body,orelse)

        update(uenv, env, location=n, file=self.filename)
        return env

    def visitClassDef(self, n):
        return {}
        
    def visitName(self, n, *vty):
        if isinstance(n.ctx, ast.Store):
            assert len(vty) == 1
            return {Var(n.id): vty[0]}
        else: return {}

    def visitTuple(self, n, vty):
        env = {}
        assert tyinstance(vty, InferBottom) or tyinstance(vty, Dyn)
        if isinstance(n.ctx, ast.Store):
            [env.update(self.dispatch(t, vty)) for t in n.elts]
        return env

    def visitList(self, n, vty):
        if isinstance(n.ctx, ast.Store):
            return self.visitTuple(n, vty)
        else: return {}
