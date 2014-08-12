from vis import Visitor
import ast, flags
from functools import reduce

class GatheringVisitor(Visitor):
    examine_functions = False

    def reduce_expr(self, ns, *args):
        return reduce(self.combine_expr, [self.dispatch(n, *args) for n in ns], 
                      self.empty_expr())

    def reduce_stmt(self, ns, *args):
        return reduce(self.combine_stmt, [self.dispatch(n, *args) for n in ns], 
                      self.empty_stmt())

    def default_expr(self, n, *args):
        return self.empty_expr()
    def default_stmt(self, n, *args):
        return self.empty_expr()
    def default(self, n, *args):
        if isinstance(n, ast.expr):
            return self.default_expr(n, *args)
        elif isinstance(n, ast.stmt):
            return self.default_stmt(n, *args)
        else: return self.empty_expr()

    def lift(self, n):
        return self.combine_stmt_expr(self.empty_stmt(), n)

    def dispatch_statements(self, ns, *args):
        if not hasattr(self, 'visitor'): # preorder may not have been called
            self.visitor = self
        return self.reduce_stmt(ns, *args)

    def visitModule(self, n, *args):
        return self.dispatch_statements(n.body, *args)

## STATEMENTS ##
    # Function stuff
    def visitFunctionDef(self, n, *args):
        largs = self.dispatch(n.args, *args)
        decorator = self.reduce_stmt(n.decorator_list, *args)
        if self.examine_functions:
            body = self.dispatch_statements(n.body, *args)
        else: body = self.empty_stmt()
        return self.combine_stmt_expr(body, self.combine_expr(largs, decorator))

    def visitarguments(self, n, *args):
        if flags.PY_VERSION == 3:
            return self.lift(self.combine_expr(self.reduce_expr(n.defaults, *args),
                                               self.reduce_expr(n.kw_defaults, *args)))
        else: return self.lift(self.reduce_expr(n.defaults, *args))

    def visitReturn(self, n, *args):
        if n.value:
            return self.lift(self.dispatch(n.value, *args))
        else: return self.default(n, *args)

    # Assignment stuff
    def visitAssign(self, n, *args):
        val = self.dispatch(n.value, *args)
        targets = self.reduce_expr(n.targets,*args)
        return self.lift(self.combine_expr(val, targets))

    def visitAugAssign(self, n, *args):
        return self.lift(self.combine_expr(self.dispatch(n.target, *args),
                                           self.dispatch(n.value, *args)))

    def visitDelete(self, n, *args):
        return self.lift(self.reduce_expr(n.targets, *args))

    # Control flow stuff
    def visitIf(self, n, *args):
        test = self.dispatch(n.test, *args)
        body = self.dispatch_statements(n.body, *args)
        orelse = self.dispatch_statements(n.orelse, *args) if n.orelse else self.empty_stmt()
        return self.combine_stmt_expr(self.combine_stmt(body, orelse),test)

    def visitFor(self, n, *args):
        target = self.dispatch(n.target, *args)
        iter = self.dispatch(n.iter, *args)
        body = self.dispatch_statements(n.body, *args)
        orelse = self.dispatch_statements(n.orelse, *args) if n.orelse else self.empty_stmt()
        return self.combine_stmt_expr(self.combine_stmt(body,orelse),self.combine_expr(target,iter))
        
    def visitWhile(self, n, *args):
        test = self.dispatch(n.test, *args)
        body = self.dispatch_statements(n.body, *args)
        orelse = self.dispatch_statements(n.orelse, *args) if n.orelse else self.empty_stmt()
        return self.combine_stmt_expr(self.combine_stmt(body,orelse),test)

    def visitWith(self, n, *args):
        body = self.dispatch_statements(n.body, *args)
        if flags.PY_VERSION == 3 and flags.PY3_VERSION >= 3:
            items = self.reduce_expr(n.items, *args)
        else:
            context = self.dispatch(n.context_expr, *args)
            optional_vars = self.dispatch(n.optional_vars, *args) if n.optional_vars else self.empty_stmt()
            items = self.combine_expr(context, optional_vars)
        return self.combine_stmt_expr(body, items)
    
    def visitwithitem(self, n, *args):
        return self.combine_expr(self.dispatch(n.context_expr, *args),
                                 self.dispatch(n.optional_vars, *args) if\
                                     n.optional_vars else self.empty_stmt())

    # Class stuff
    def visitClassDef(self, n, *args):
        bases = self.reduce_expr(n.bases, *args)
        if flags.PY_VERSION == 3:
            keywords = reduce(self.combine_expr, [self.dispatch(kwd.value, *args) for kwd in n.keywords], self.empty_expr())
        else: keywords = self.empty_expr()
        body = self.dispatch_statements(n.body, *args)
        return self.combine_stmt_expr(self.combine_expr(keywords,bases),body)

    # Exception stuff
    # Python 2.7, 3.2
    def visitTryExcept(self, n, *args):
        body = self.dispatch_statements(n.body, *args)
        handlers = self.reduce_stmt(n.handlers, *args)
        orelse = self.dispatch_statements(n.orelse, *args) if n.orelse else self.empty_stmt()
        return self.combine_stmt(self.combine_stmt(handlers,body),orelse)

    # Python 2.7, 3.2
    def visitTryFinally(self, n, *args):
        body = self.dispatch_statements(n.body, *args)
        finalbody = self.dispatch_statements(n.finalbody, *args)
        return self.combine_stmt(body, finalbody)
    
    # Python 3.3
    def visitTry(self, n, *args):
        body = self.dispatch_statements(n.body, *args)
        handlers = self.reduce_stmt(n.handlers, *args)
        orelse = self.dispatch_statements(n.orelse, *args) if n.orelse else self.empty_stmt()
        finalbody = self.dispatch_statements(n.finalbody, *args)
        return self.combine_stmt(self.combine_stmt(handlers,body),self.combine_stmt(finalbody,orelse))

    def visitExceptHandler(self, n, *args):
        ty = self.dispatch(n.type, *args) if n.type else self.empty_expr()
        body = self.dispatch_statements(n.body, *args)
        return self.combine_stmt_expr(body, ty)

    def visitRaise(self, n, *args):
        if flags.PY_VERSION == 3:
            exc = self.dispatch(n.exc, *args) if n.exc else self.empty_expr()
            cause = self.dispatch(n.cause, *args) if n.cause else self.empty_expr()
            return self.lift(self.combine_expr(exc,cause))
        elif flags.PY_VERSION == 2:
            type = self.dispatch(n.type, *args) if n.type else self.empty_expr()
            inst = self.dispatch(n.inst, *args) if n.inst else self.empty_expr()
            tback = self.dispatch(n.tback, *args) if n.tback else self.empty_expr()
            return self.lift(self.combine_expr(type, self.combine_expr(inst, tback)))

    def visitAssert(self, n, *args):
        test = self.dispatch(n.test, *args)
        msg = self.dispatch(n.msg, *args) if n.msg else self.empty_expr()
        return self.lift(self.combine_expr(test, msg))

    # Miscellaneous
    def visitExpr(self, n, *args):
        return self.lift(self.dispatch(n.value, *args))

    def visitPrint(self, n, *args):
        dest = self.dispatch(n.dest, *args) if n.dest else self.empty_expr()
        values = self.reduce_expr(n.values,*args)
        return self.lift(self.combine_expr(dest, values))

    def visitExec(self, n, *args):
        body = self.dispatch(n.body, *args)
        globals = self.dispatch(n.globals, *args) if n.globals else self.empty_expr()
        locals = self.dispatch(n.locals, *args) if n.locals else self.empty_expr()
        return self.lift(self.combine_expr(self.combine_expr(body, globals), locals))

### EXPRESSIONS ###
    # Op stuff
    def visitBoolOp(self, n, *args):
        return self.reduce_expr(n.values,*args)

    def visitBinOp(self, n, *args):
        return self.combine_expr(self.dispatch(n.left, *args),
                            self.dispatch(n.right, *args))

    def visitUnaryOp(self, n, *args):
        return self.dispatch(n.operand, *args)

    def visitCompare(self, n, *args):
        left = self.dispatch(n.left, *args)
        comparators = self.reduce_expr(n.comparators,*args)
        return self.combine_expr(left, comparators)

    # Collections stuff    
    def visitList(self, n, *args):
        return self.reduce_expr(n.elts,*args)

    def visitTuple(self, n, *args):
        return self.reduce_expr(n.elts,*args)

    def visitDict(self, n, *args):
        return self.combine_expr(self.reduce_expr(n.keys,*args),
                            self.reduce_expr(n.values,*args))

    def visitSet(self, n, *args):
        return self.reduce_expr(n.elts,*args)

    def visitListComp(self, n,*args):
        generators = self.reduce_expr(n.generators,*args)
        elt = self.dispatch(n.elt, *args)
        return self.combine_expr(generators, elt)

    def visitSetComp(self, n, *args):
        generators = self.reduce_expr(n.generators,*args)
        elt = self.dispatch(n.elt, *args)
        return self.combine_expr(generators, elt)

    def visitDictComp(self, n, *args):
        generators = self.reduce_expr(n.generators,*args)
        key = self.dispatch(n.key, *args)
        value = self.dispatch(n.value, *args)
        return self.combine_expr(self.combine_expr(generators, key), value)

    def visitGeneratorExp(self, n, *args):
        generators = self.reduce_expr(n.generators,*args)
        elt = self.dispatch(n.elt, *args)
        return self.combine_expr(generators, elt)

    def visitcomprehension(self, n, *args):
        iter = self.dispatch(n.iter, *args)
        ifs = self.reduce_expr(n.ifs, *args)
        target = self.dispatch(n.target, *args)
        return self.combine_expr(self.combine_expr(iter, ifs), target)

    # Control flow stuff
    def visitYield(self, n, *args):
        return self.dispatch(n.value, *args) if n.value else self.default(n, *args)

    def visitYieldFrom(self, n, *args):
        return self.dispatch(n.value, *args)

    def visitIfExp(self, n, *args):
        test = self.dispatch(n.test, *args)
        body = self.dispatch(n.body, *args)
        orelse = self.dispatch(n.orelse, *args)
        return self.combine_expr(self.combine_expr(test,body),orelse)

    # Function stuff
    def visitCall(self, n, *args):
        func = self.dispatch(n.func, *args)
        argdata = self.reduce_expr(n.args, *args)
        return self.combine_expr(func, argdata)

    def visitLambda(self, n, *args):
        largs = self.dispatch(n.args, *args)
        body = self.dispatch(n.body, *args)
        return self.combine_expr(largs, body)

    # Variable stuff
    def visitAttribute(self, n, *args):
        return self.dispatch(n.value, *args)

    def visitSubscript(self, n, *args):
        value = self.dispatch(n.value, *args)
        slice = self.dispatch(n.slice, *args)
        return self.combine_expr(value, slice)

    def visitIndex(self, n, *args):
        return self.dispatch(n.value, *args)

    def visitSlice(self, n, *args):
        lower = self.dispatch(n.lower, *args) if n.lower else self.empty_expr()
        upper = self.dispatch(n.upper, *args) if n.upper else self.empty_expr()
        step = self.dispatch(n.step, *args) if n.step else self.empty_expr()
        return self.combine_expr(self.combine_expr(lower, upper), step)

    def visitExtSlice(self, n, *args):
        return self.reduce_expr(n.dims, *args)

    def visitStarred(self, n, *args):
        return self.dispatch(n.value, *args)

class SetGatheringVisitor(GatheringVisitor):
    def combine_expr(self, s1, s2):
        return set.union(s1,s2)
    combine_stmt = combine_expr
    combine_stmt_expr = combine_expr
    empty_stmt = set
    empty_expr = set
    
class DictGatheringVisitor(GatheringVisitor):
    def combine_expr(self, s1, s2):
        s1.update(s2)
        return s1
    combine_stmt = combine_expr
    combine_stmt_expr = combine_expr
    empty_stmt = dict
    empty_expr = dict

class ListGatheringVisitor(GatheringVisitor):
    def combine_expr(self, s1, s2):
        return s1 + s2
    combine_stmt = combine_expr
    combine_stmt_expr = combine_expr
    empty_stmt = list
    empty_expr = list

class BooleanOrVisitor(GatheringVisitor):
    def combine_expr(self, s1, s2):
        return s1 or s2
    combine_stmt = combine_expr
    combine_stmt_expr = combine_expr
    empty_stmt = lambda *x: False
    empty_expr = lambda *x: False
