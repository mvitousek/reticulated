from rtypes import *
from typing import Var, warn
from visitors import *
import os.path, ast

class Classfinder(DictGatheringVisitor):
    examine_functions = False
    def combine_stmt(self, scope1, scope2):
        for x in scope2:
            if x in scope1:
                scope1[x] = Dyn
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

class Inheritfinder(SetGatheringVisitor):
    examine_functions = False
    def visitClassDef(self, n):
        inherits = set()
        for base in n.bases:
            if isinstance(base, ast.Name):
                inherits.add(base.id)
            else: warn('Cannot typecheck subtypes of non-trivial class names', 1)
        return {(n.name, inh) for inh in inherits}

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
        mfo = self.dispatch_statements(n.body)
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

class WrongContextVisitor(SetGatheringVisitor):
    examine_functions = True

    def dispatch_scope(self, n, *args):
        return self.dispatch_statements(n, *args)
        
    def visitAssign(self, n, *args):
        val = self.dispatch(n.value)
        targets = self.reduce_expr(n.targets,ast.Store)
        return self.lift(self.combine_expr(val, targets))

    def visitAugAssign(self, n, *args):
        return self.lift(self.combine_expr(self.dispatch(n.target, ast.Store),
                                           self.dispatch(n.value)))
    
    def visitDelete(self, n, *args):
        return self.lift(self.reduce_expr(n.targets, ast.Del))

    def visitFor(self, n, *args):
        target = self.dispatch(n.target, ast.Store)
        iter = self.dispatch(n.iter, *args)
        body = self.dispatch_statements(n.body, *args)
        orelse = self.dispatch_statements(n.orelse, *args) if n.orelse else self.empty_stmt()
        return self.combine_stmt_expr(self.combine_stmt(body,orelse),self.combine_expr(target,iter))

    def visitWith(self, n, *args):
        body = self.dispatch_statements(n.body, *args)
        if flags.PY_VERSION == 3 and flags.PY3_VERSION == 3:
            items = self.reduce_expr(n.items, *args)
        else:
            context = self.dispatch(n.context_expr, *args)
            optional_vars = self.dispatch(n.optional_vars, ast.Store) if n.optional_vars else self.empty_stmt()
            items = self.combine_expr(context, optional_vars)
        return self.combine_stmt_expr(body, items)
    
    def visitwithitem(self, n, *args):
        return self.combine_expr(self.dispatch(n.context_expr, *args),
                                 self.dispatch(n.optional_vars, ast.Store) if\
                                     n.optional_vars else self.empty_stmt())

    def visitcomprehension(self, n, *args):
        iter = self.dispatch(n.iter, *args)
        ifs = self.reduce_expr(n.ifs, *args)
        target = self.dispatch(n.target, ast.Store)
        return self.combine_expr(self.combine_expr(iter, ifs), target)

    def visitAttribute(self, n, ctx=ast.Load):
        assert isinstance(n.ctx, ctx), '%s:%d\n%s' % (self.filename, n.lineno, ast.dump(n))
        return self.dispatch(n.value)

    def visitSubscript(self, n, ctx=ast.Load):
        assert isinstance(n.ctx, ctx), '%s:%d\n%s' % (self.filename, n.lineno, ast.dump(n))
        value = self.dispatch(n.value)
        slice = self.dispatch(n.slice)
        return self.combine_expr(value, slice)

    def visitStarred(self, n, ctx=ast.Load):
        assert isinstance(n.ctx, ctx), '%s:%d\n%s' % (self.filename, n.lineno, ast.dump(n))
        return self.dispatch(n.value, ctx)

    def visitList(self, n, ctx=ast.Load):
        assert isinstance(n.ctx, ctx), '%s:%d\n%s' % (self.filename, n.lineno, ast.dump(n))
        return self.reduce_expr(n.elts,ctx)

    def visitTuple(self, n, ctx=ast.Load):
        assert isinstance(n.ctx, ctx), '%s:%d\n%s' % (self.filename, n.lineno, ast.dump(n))
        return self.reduce_expr(n.elts,ctx)

    def visitName(self, n, ctx=ast.Load):
        assert isinstance(n.ctx, ctx), '%s:%d\n%s' % (self.filename, n.lineno, ast.dump(n))
        return set()

class ClassDynamizationVisitor(BooleanOrVisitor):
    examine_functions = True
    def visitName(self, n):
        return n.id in {'setattr', 'delattr', 'property'}
    def visitFunctionDef(self, n):
        return n.name == '__new__'
