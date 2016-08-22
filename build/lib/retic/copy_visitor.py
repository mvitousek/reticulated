from .vis import Visitor
import ast
from . import flags, ast_trans, retic_ast

class CopyVisitor(Visitor):
    # Copies AST nodes. Inherit from this visitor to create visitors
    # that output modified versions of their input ASTs.
    #
    # Very important: the copy visitor by default doesn't explore
    # functiondefinitions. A subclass of CopyVistor that SHOULD
    # explore function definitions must set the class field examine_functions to True.
    #
    # Any visitor should be invoked at the top level using .preorder, and
    # any recursive calls should be made using .dispatch.

    examine_functions = False

    def reduce(self, ns, *args):
        return [self.dispatch(n, *args) for n in ns]

    def dispatch_scope(self, ns, *args):
        return [self.dispatch(s, *args) for s in ns]

    def dispatch_statements(self, ns, *args):
        if not hasattr(self, 'visitor'): # preorder may not have been called
            self.visitor = self
        return [self.dispatch(s, *args) for s in ns]

    def visitModule(self, n, *args):
        body = self.dispatch_scope(n.body, *args)
        return ast.Module(body=body)

    def dispatch(self, n, *args):
        res = super().dispatch(n, *args)
        tys = [ast.stmt, ast.expr, ast.excepthandler]
        if flags.PY_VERSION >= 3 and flags.PY3_VERSION >= 4:
            tys.append(ast.arg)
        if any(isinstance(res, ty) for ty in tys):
            res.lineno = n.lineno
            res.col_offset = n.col_offset
        if hasattr(n, 'retic_type'):
            res.retic_type = n.retic_type
        if hasattr(n, 'retic_import_aliases'):
            res.retic_import_aliases = n.retic_import_aliases
        return res

    def visitlist(self, ns, *args):
        return [self.dispatch(s, *args) for s in ns]
    
    def visitNoneType(self, ns, *args):
        return None

## CUSTOM NODES ##
    def visitCheck(self, n, *args):
        return retic_ast.Check(value=self.dispatch(n.value, *args), type=n.type, lineno=n.lineno, col_offset=n.col_offset)

    def visitExpandSeq(self, n, *args):
        return retic_ast.ExpandSeq(body=self.dispatch_statements(n.body, *args), lineno=n.lineno, col_offset=n.col_offset)

## STATEMENTS ##
    # Function stuff
    def visitFunctionDef(self, n, *args):
        fargs = self.dispatch(n.args, *args)
        decorator_list = [self.dispatch(dec, *args) for dec in n.decorator_list]
        if self.examine_functions:
            body = self.dispatch_scope(n.body, *args)
        else: body = n.body
        if flags.PY_VERSION == 3:
            return ast.FunctionDef(name=n.name, args=fargs,
                                   body=body, decorator_list=decorator_list,
                                   returns=n.returns, lineno=n.lineno)
        elif flags.PY_VERSION == 2:
            return ast.FunctionDef(name=n.name, args=fargs,
                                   body=body, decorator_list=decorator_list,
                                   lineno=n.lineno)

    def visitarguments(self, n, *args):
        fargs = [self.dispatch(arg, *args) for arg in n.args]
        vararg = self.dispatch(n.vararg, *args) if n.vararg else None 
        defaults = [self.dispatch(default, *args) for default in n.defaults]
        if flags.PY_VERSION == 3:
            kwonlyargs = self.reduce(n.kwonlyargs, *args)
            kw_defaults = [self.dispatch(default, *args) for default in n.kw_defaults]
            
            if flags.PY3_VERSION <= 3:
                varargannotation = self.dispatch(n.varargannotation, *args) if n.varargannotation else None
                kwargannotation = self.dispatch(n.kwargannotation, *args) if n.kwargannotation else None
                return ast.arguments(args=fargs, vararg=vararg, varargannotation=varargannotation,
                                     kwonlyargs=kwonlyargs, kwarg=n.kwarg,
                                     kwargannotation=kwargannotation, defaults=defaults, kw_defaults=kw_defaults)
            else:
                return ast.arguments(args=fargs, vararg=vararg,
                                     kwonlyargs=kwonlyargs, kwarg=n.kwarg,
                                     defaults=defaults, kw_defaults=kw_defaults)
        elif flags.PY_VERSION == 2:
            return ast.arguments(args=fargs, vararg=vararg, kwarg=n.kwarg, defaults=defaults)

    def visitarg(self, n, *args):
        annotation = self.dispatch(n.annotation, *args) if n.annotation else None
        return ast.arg(arg=n.arg, annotation=annotation)

    def visitReturn(self, n, *args):
        value = self.dispatch(n.value, *args) if n.value else None
        return ast.Return(value=value, lineno=n.lineno)

    # Assignment stuff
    def visitAssign(self, n, *args):
        val = self.dispatch(n.value, *args)
        targets = [self.dispatch(target,*args) for target in n.targets]
        return ast.Assign(targets=targets, value=val, lineno=n.lineno)

    def visitAugAssign(self, n, *args):
        return ast.AugAssign(target=self.dispatch(n.target, *args),
                             op=n.op,
                             value=self.dispatch(n.value, *args))

    def visitDelete(self, n, *args):
        return ast.Delete(targets=[self.dispatch(target,*args) for target in n.targets])

    # Control flow stuff
    def visitIf(self, n, *args):
        return ast.If(test=self.dispatch(n.test, *args),
                      body=self.dispatch_statements(n.body, *args),
                      orelse=self.dispatch_statements(n.orelse, *args))

    def visitFor(self, n, *args):
        return ast.For(target=self.dispatch(n.target, *args),
                       iter=self.dispatch(n.iter, *args),
                       body=self.dispatch_statements(n.body, *args),
                       orelse=self.dispatch_statements(n.orelse, *args))

    def visitWhile(self, n, *args):
        return ast.While(test=self.dispatch(n.test, *args),
                         body=self.dispatch_statements(n.body, *args),
                         orelse=self.dispatch_statements(n.orelse, *args))

    def visitWith(self, n, *args): 
        body = self.dispatch_statements(n.body, *args)
        if flags.PY_VERSION == 3 and flags.PY3_VERSION >= 3:
            items = [self.dispatch(item, *args) for item in n.items]
            return ast.With(items=items, body=body)
        else:
            context = self.dispatch(n.context_expr, *args)
            optional_vars = self.dispatch(n.optional_vars, *args) if n.optional_vars else None
            return ast.With(context_expr=context, optional_vars=optional_vars, body=body)

    def visitwithitem(self, n, *args):
        return ast.withitem(context_expr=self.dispatch(n.context_expr, *args),
                            optional_vars=(self.dispatch(n.optional_vars, *args) if n.optional_vars else None))
            

    # Class stuff
    def visitClassDef(self, n, *args):
        bases = self.reduce(n.bases, *args)
        starargs = self.dispatch(n.starargs, *args) if getattr(n, 'starargs', None) else None
        kwargs = self.dispatch(n.kwargs, *args) if getattr(n, 'kwargs', None) else None
        decorator_list = self.reduce(n.decorator_list, *args)
        body = self.dispatch_statements(n.body, *args)
        keywords = [ast.keyword(k.arg, self.dispatch(k.value, *args)) for k in \
                    getattr(n, 'keywords', [])]
        return ast_trans.ClassDef(name=n.name, 
                                  bases=bases,
                                  keywords=keywords,
                                  starargs=starargs,
                                  kwargs=kwargs,
                                  body=body,
                                  decorator_list=decorator_list)
            

    # Exception stuff
    # Python 2.7, 3.2
    def visitTryExcept(self, n, *args):
        body = self.dispatch_statements(n.body, *args)
        handlers = self.reduce(n.handlers, *args)
        orelse = self.dispatch_statements(n.orelse, *args)
        return ast.TryExcept(body=body, handlers=handlers, orelse=orelse)

    # Python 2.7, 3.2
    def visitTryFinally(self, n, *args):
        body = self.dispatch_statements(n.body, *args)
        finalbody = self.dispatch_statements(n.finalbody, *args)
        return ast.TryFinally(body, finalbody)
    
    # Python 3.3
    def visitTry(self, n, *args):
        body = self.dispatch_statements(n.body, *args)
        handlers = self.reduce(n.handlers, *args)
        orelse = self.dispatch_statements(n.orelse, *args)
        finalbody = self.dispatch_statements(n.finalbody, *args)
        return ast.Try(body=body, handlers=handlers,orelse=orelse,finalbody=finalbody)

    def visitExceptHandler(self, n, *args):
        return ast.ExceptHandler(type=self.dispatch(n.type, *args) if n.type else None,
                                 name=n.name,
                                 body=self.dispatch_statements(n.body, *args))

    def visitRaise(self, n, *args):
        if flags.PY_VERSION == 3:
            exc = self.dispatch(n.exc, *args) if n.exc else None
            cause = self.dispatch(n.cause, *args) if n.cause else None
            return ast.Raise(exc=exc, cause=cause)
        elif flags.PY_VERSION == 2:
            type = self.dispatch(n.type, *args) if n.type else None
            inst = self.dispatch(n.inst, *args) if n.inst else None
            tback = self.dispatch(n.tback, *args) if n.tback else None
            return ast.Raise(type=type, inst=inst, tback=tback)

    def visitAssert(self, n, *args):
        test = self.dispatch(n.test, *args)
        msg = self.dispatch(n.msg, *args) if n.msg else None
        return ast.Assert(test=test,msg=msg)

    # Miscellaneous
    def visitExpr(self, n, *args):
        return ast.Expr(self.dispatch(n.value, *args))

    def visitPrint(self, n, *args):
        dest = self.dispatch(n.dest, *args) if n.dest else None
        values = self.reduce(n.values, *args)
        return ast.Print(dest=dest, values=values, nl=n.nl)

    def visitExec(self, n, *args):
        body = self.dispatch(n.body, *args)
        globals = self.dispatch(n.globals, *args) if n.globals else None
        locals = self.dispatch(n.locals, *args) if n.locals else None
        return ast.Exec(body=body, globals=globals, locals=locals)

    def visitImport(self, n, *args):
        return n
    def visitImportFrom(self, n, *args):
        return n
    def visitPass(self, n, *args):
        return n
    def visitBreak(self, n, *args):
        return n
    def visitContinue(self, n, *args):
        return n

### EXPRESSIONS ###
    # Op stuff
    def visitBoolOp(self, n, *args):
        return ast.BoolOp(op=n.op,
                          values=self.reduce(n.values, *args))

    def visitBinOp(self, n, *args):
        return ast.BinOp(left=self.dispatch(n.left, *args),
                         op=n.op,
                         right=self.dispatch(n.right, *args))

    def visitUnaryOp(self, n, *args):
        return ast.UnaryOp(op=n.op, operand=self.dispatch(n.operand, *args))

    def visitCompare(self, n, *args):
        left = self.dispatch(n.left, *args)
        comparators = self.reduce(n.comparators,*args)
        return ast.Compare(left=left, ops=n.ops, comparators=comparators)
        
    # Collections stuff    
    def visitList(self, n, *args):
        return ast.List(elts=self.reduce(n.elts,*args), ctx=n.ctx)

    def visitTuple(self, n, *args):
        return ast.Tuple(elts=self.reduce(n.elts,*args), ctx=n.ctx)

    def visitDict(self, n, *args):
        return ast.Dict(keys=self.reduce(n.keys,*args),
                        values=self.reduce(n.values,*args))

    def visitSet(self, n, *args):
        return ast.Set(elts=self.reduce(n.elts,*args))

    def visitListComp(self, n,*args):
        generators = self.reduce(n.generators,*args)
        elt = self.dispatch(n.elt, *args)
        return ast.ListComp(elt=elt, generators=generators)

    def visitSetComp(self, n, *args):
        generators = self.reduce(n.generators,*args)
        elt = self.dispatch(n.elt, *args)
        return ast.SetComp(elt=elt, generators=generators)

    def visitDictComp(self, n, *args):
        generators = self.reduce(n.generators,*args)
        key = self.dispatch(n.key, *args)
        value = self.dispatch(n.value, *args)
        return ast.DictComp(key=key, value=value, generators=generators)

    def visitGeneratorExp(self, n, *args):
        generators = self.reduce(n.generators,*args)
        elt = self.dispatch(n.elt, *args)
        return ast.GeneratorExp(elt=elt, generators=generators)

    def visitcomprehension(self, n, *args):
        iter = self.dispatch(n.iter, *args)
        ifs = self.reduce(n.ifs, *args)
        target = self.dispatch(n.target, *args)
        return ast.comprehension(target=target, iter=iter, ifs=ifs)

    # Control flow stuff
    def visitYield(self, n, *args):
        return ast.Yield(self.dispatch(n.value, *args) if n.value else None)

    def visitYieldFrom(self, n, *args):
        return ast.YieldFrom(self.dispatch(n.value, *args))

    def visitIfExp(self, n, *args):
        test = self.dispatch(n.test, *args)
        body = self.dispatch(n.body, *args)
        orelse = self.dispatch(n.orelse, *args)
        return ast.IfExp(test=test, body=body, orelse=orelse)

    # Function stuff
    def visitCall(self, n, *args):
        return ast_trans.Call(func=self.dispatch(n.func, *args),
                              args=self.reduce(n.args, *args),
                              keywords=[ast.keyword(arg=k.arg, value=self.dispatch(k.value, *args))\
                                        for k in n.keywords],
                              starargs=self.dispatch(n.starargs, *args) if getattr(n, 'starargs', None) else None,
                              kwargs=self.dispatch(n.kwargs, *args) if getattr(n, 'kwargs', None) else None)

    def visitLambda(self, n, *args):
        largs = self.dispatch(n.args, *args)
        body = self.dispatch(n.body, *args)
        return ast.Lambda(args=largs, body=body)

    # Variable stuff
    def visitAttribute(self, n, *args):
        return ast.Attribute(value=self.dispatch(n.value, *args),
                             attr=n.attr, ctx=n.ctx)

    def visitSubscript(self, n, *args):
        value = self.dispatch(n.value, *args)
        slice = self.dispatch(n.slice, *args)
        return ast.Subscript(value=value, slice=slice, ctx=n.ctx)

    def visitIndex(self, n, *args):
        return ast.Index(value=self.dispatch(n.value, *args))

    def visitSlice(self, n, *args):
        lower = self.dispatch(n.lower, *args) if n.lower else None
        upper = self.dispatch(n.upper, *args) if n.upper else None
        step = self.dispatch(n.step, *args) if n.step else None
        return ast.Slice(lower=lower,upper=upper,step=step)

    def visitExtSlice(self, n, *args):
        return ast.ExtSlice(dims=self.reduce(n.dims, *args))

    def visitStarred(self, n, *args):
        return ast.Starred(value=self.dispatch(n.value, *args), ctx=n.ctx)

    def visitNameConstant(self, n, *args):
        return n
    def visitName(self, n, *args):
        return n
    def visitNum(self, n, *args):
        return n
    def visitStr(self, n, *args):
        return n
    def visitBytes(self, n, *args):
        return n
    def visitEllipsis(self, n, *args):
        return n
    
    def visitGlobal(self, n, *args):
        return n

    def visitNonlocal(self, n, *args):
        return n


if __name__ == '__main__':
    x = '''
def f(x):
    try:
      return x * x
    except Foo as Bar:
      with f(x, y=320) as _z:
        boo[32:21:5][2][5][7]
f(5)
'''
    xast = ast.parse(x)
    yast = CopyVisitor().preorder(xast)
    assert ast.dump(xast) == ast.dump(yast), '\n'+ ast.dump(xast) + '\n\n\n' + ast.dump(yast)
