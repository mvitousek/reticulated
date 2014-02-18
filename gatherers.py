from rtypes import *
from typing import Var
from visitors import DictGatheringVisitor, GatheringVisitor, SetGatheringVisitor
import os.path, ast

class Classfinder(DictGatheringVisitor):
    examine_functions = False
    def combine_stmt(self, scope1, scope2):
        for x in scope2:
            if x in scope1:
                scope1[x] = typing.Dyn
            else: scope1[x] = scope2[x]
        return scope1
    def combine_expr(self, scope1, scope2):
        return {}
    def combine_stmt_expr(self, stmt, expr):
        return stmt
    def visitClassDef(self, n):
        internal_defs = self.dispatch_statements(n.body)
        internal_defs = { ('%s.%s' % (n.name, k)):internal_defs[k] for k in internal_defs}
        return { n.name : ObjectAlias(n.name, internal_defs) }

class Killfinder(SetGatheringVisitor):
    examine_functions = False
    def visitGlobal(self, n):
        return set(n.names)
    def visitNonlocal(self, n):
        return set(n.names)
    def visitClassDef(self, n):
        return set()

class Aliasfinder(DictGatheringVisitor):
    examine_functions = False
    def visitClassDef(self, n, env):
        cls = env.get(Var(n.name), Dyn)
        inst = cls.instance() if tyinstance(cls, Class) else Dyn
        return {n.name:inst, (n.name + '.Class'):cls}
        

WILL_FALL_OFF = 2
MAY_FALL_OFF = 1
WILL_RETURN = 0

class FallOffVisitor(GatheringVisitor):
    def combine_stmt(self, m1, m2):
        return max(m1, m2)
    def combine_stmt_expr(self, stmt, expr):
        return stmt
    def combine_expr(self, e1, e2):
        return MAY_FALL_OFF
    empty_stmt = lambda *args: MAY_FALL_OFF
    empty_expr = lambda *args: MAY_FALL_OFF
    def dispatch_statements(self, ns):
        if not hasattr(self, 'visitor'): # preorder may not have been called
            self.visitor = self
        fo = MAY_FALL_OFF
        for s in ns:
            fo = self.dispatch(s)
            if fo == WILL_FALL_OFF:
                return fo
        return fo
    def visitBreak(self, n):
        return WILL_FALL_OFF
    def visitReturn(self, n):
        return WILL_RETURN if n.value else MAY_FALL_OFF
    def visitTryFinally(self, n):
        bfo = self.dispatch_statements(n.body)
        ffo = self.dispatch_statements(n.finalbody)
        if ffo == WILL_RETURN:
            return ffo
        else: return bfo
    def visitTry(self, n):
        mfo = self.dispatch_statements(n.body, env, misc)
        handlers = []
        for handler in n.handlers:
            hfo = self.dispatch(handler)
            mfo = self.combine_stmt(mfo, hfo)
        efo = self.dispatch(n.orelse) if n.orelse else mfo
        mfo = self.combine_stmt(mfo, efo)
        ffo = self.dispatch_statements(n.finalbody)
        if ffo == WILL_RETURN:
            return ffo
        else:
            return mfo
    def visitRaise(self, n):
        return WILL_RETURN
