from __future__ import print_function
import ast
from vis import Visitor
from gatherers import FallOffVisitor, WILL_RETURN
from typefinder import Typefinder
from inference import InferVisitor
from typing import *
from relations import *
from exc import StaticTypeError, UnimplementedException
import typing, ast, utils, flags

class Misc(object):
    ret = Void
    cls = None
    receiver = None
    methodscope = False
    def __init__(self, **kwargs):
        self.ret = kwargs.get('ret', Void)
        self.cls = kwargs.get('cls', None)
        self.receiver = kwargs.get('receiver', None)
        self.methodscope = kwargs.get('methodscope', False)

##Cast insertion functions##
#Normal casts
def cast(env, ctx, val, src, trg, msg, cast_function='retic_cast'):
    src = normalize(src)
    trg = normalize(trg)

    lineno = str(val.lineno) if hasattr(val, 'lineno') else 'number missing'
    merged = merge(src, trg)
    if not subcompat(src, trg, env, ctx):
        return error("%s: cannot cast from %s to %s (line %s)" % (msg, src, trg, lineno))
    elif src == merged:
        return val
    elif not flags.OPTIMIZED_INSERTION:
        warn('Inserting cast at line %s: %s => %s' % (lineno, src, trg), 1)
        return ast.Call(func=ast.Name(id=cast_function, ctx=ast.Load()),
                        args=[val, src.to_ast(), merged.to_ast(), ast.Str(s=msg)],
                        keywords=[], starargs=None, kwargs=None)
    else:
        if flags.SEMANTICS == 'MONO':
            warn('Inserting cast at line %s: %s => %s' % (lineno, src, trg), 1)
            return ast.Call(func=ast.Name(id=cast_function, ctx=ast.Load()),
                            args=[val, src.to_ast(), merged.to_ast(), ast.Str(s=msg)],
                            keywords=[], starargs=None, kwargs=None)
        elif flags.SEMANTICS == 'CAC':
            warn('Inserting cast at line %s: %s => %s' % (lineno, src, trg), 1)
            return ast.Call(func=ast.Name(id=cast_function, ctx=ast.Load()),
                            args=[val, src.to_ast(), merged.to_ast(), ast.Str(s=msg)],
                            keywords=[], starargs=None, kwargs=None)
        elif flags.SEMANTICS == 'GUARDED':
            warn('Inserting cast at line %s: %s => %s' % (lineno, src, trg), 1)
            return ast.Call(func=ast.Name(id=cast_function, ctx=ast.Load()),
                            args=[val, src.to_ast(), merged.to_ast(), ast.Str(s=msg)],
                            keywords=[], starargs=None, kwargs=None)
        else: raise UnimplementedException('efficient insertion unimplemented for this semantics')

# Casting with unknown source type, as in cast-as-assertion 
# function return values at call site
def check(val, trg, msg, check_function='retic_check', lineno=None):
    trg = normalize(trg)
    if lineno == None:
        lineno = str(val.lineno) if hasattr(val, 'lineno') else 'number missing'

    if not flags.OPTIMIZED_INSERTION:
        warn('Inserting check at line %s: %s' % (lineno, trg), 1)
        return ast.Call(func=ast.Name(id=check_function, ctx=ast.Load()),
                        args=[val, trg.to_ast(), ast.Str(s=msg)],
                        keywords=[], starargs=None, kwargs=None)
    else:
        if flags.SEMANTICS == 'CAC':
            warn('Inserting check at line %s: %s' % (lineno, trg), 1)
            return ast.Call(func=ast.Name(id=check_function, ctx=ast.Load()),
                            args=[val, trg.to_ast(), ast.Str(s=msg)],
                            keywords=[], starargs=None, kwargs=None)
        else: return val

# Check, but within an expression statement
def check_stmtlist(val, trg, msg, check_function='retic_check', lineno=None):
    chkval = check(val, trg, msg, check_function, lineno)
    if not flags.OPTIMIZED_INSERTION:
        return [ast.Expr(value=chkval, lineno=lineno)]
    else:
        if chkval == val:
            return []
        else: return [ast.Expr(value=chkval, lineno=lineno)]

# Insert a call to an error function if we've turned off static errors
def error(msg, error_function='retic_error'):
    if flags.STATIC_ERRORS:
        raise StaticTypeError(msg)
    else:
        warn('Static error found',2)
        return ast.Call(func=ast.Name(id=error_function, ctx=ast.Load()),
                        args=[ast.Str(s=msg+' (statically detected)')], keywords=[], starargs=None,
                        kwargs=None)

# Error, but within an expression statement
def error_stmt(msg, lineno, error_function='retic_error'):
    if flags.STATIC_ERRORS:
        raise StaticTypeError(msg)
    else:
        return [ast.Expr(value=error(msg, error_function), lineno=lineno)]

class Typechecker(Visitor):
    typefinder = Typefinder()
    infervisitor = InferVisitor()
    falloffvisitor = FallOffVisitor()
    
    def dispatch_debug(self, tree, *args):
        ret = super().dispatch(tree, *args)
        print('results of %s:' % tree.__class__.__name__)
        if isinstance(ret, tuple):
            if isinstance(ret[0], ast.AST):
                print(ast.dump(ret[0]))
            if isinstance(ret[1], PyType):
                print(ret[1])
        if isinstance(ret, ast.AST):
            print(ast.dump(misc))
        return ret

    if flags.DEBUG_VISITOR:
        dispatch = dispatch_debug

    def typecheck(self, n):
        n = ast.fix_missing_locations(n)
        n, env = self.preorder(n, {})
        n = ast.fix_missing_locations(n)
        return n, env

    def dispatch_scope(self, n, env, misc, initial_locals=None):
        if initial_locals == None:
            initial_locals = {}
        env = env.copy()
        try:
            uenv, locals = self.typefinder.dispatch_scope(n, env, initial_locals, type_inference=True)
        except StaticTypeError as exc:
            if flags.STATIC_ERRORS:
                raise exc
            else:
                return error_stmt(exc.args[0]) 
        env.update(uenv)
        locals = locals.keys()
        env = self.infervisitor.infer(self, locals, n, env, misc)
        print('Post-inference typing:', env)
        body = []
        for s in n:
            stmts = self.dispatch(s, env, misc)
            body += stmts
        return body, env

    def dispatch_class(self, n, env, misc, initial_locals=None):
        def aliases(env):
            nenv = {}
            for k in env:
                if isinstance(k, TypeVariable):
                    nenv[k.name] = env[k]
            return nenv
        if initial_locals == None:
            initial_locals = {}
        env = env.copy()
        try:
            uenv, _ = self.typefinder.dispatch_scope(n, env, initial_locals, 
                                                     tyenv=aliases(env), type_inference=False)
        except StaticTypeError as exc:
            if flags.STATIC_ERRORS:
                raise exc
            else:
                return error_stmt(exc.args[0])
        env.update(uenv)
        body = []
        for s in n:
            stmts = self.dispatch(s, env, misc)
            body += stmts
        return body

    def dispatch_statements(self, n, env, misc):
        body = []
        for s in n:
            stmts = self.dispatch(s, env, misc)
            body += stmts
        return body
        
    def visitModule(self, n, env):
        body, env = self.dispatch_scope(n.body, env, Misc())
        return ast.Module(body=body), env

    def default(self, n, *args):
        if isinstance(n, ast.expr):
            return n, Dyn
        elif isinstance(n, ast.stmt):
            return [n]
        else: n

## STATEMENTS ##
    # Import stuff
    def visitImport(self, n, env, misc):
        return [n]

    def visitImportFrom(self, n, env, misc):
        return [n]

    # Function stuff
    def visitFunctionDef(self, n, env, misc): #TODO: check defaults, handle varargs and kwargs
        nty = env[Var(n.name)]
        args, argnames = self.dispatch(n.args, env, nty, misc)
        decorator_list = [self.dispatch(dec, env, misc)[0] for dec in n.decorator_list if not is_annotation(dec)]
        
        env = env.copy()

        if misc.cls:
            receiver = None if not misc.methodscope else ast.Name(id=argnames[0], ctx=ast.Load())
        else: 
            receiver = None

        argtys = list(zip([Var(x) for x in argnames], nty.froms))
        initial_locals = dict(argtys + [(Var(n.name), nty)])

        
        body, _ = self.dispatch_scope(n.body, env, Misc(ret=nty.to, cls=misc.cls, receiver=receiver), 
                                   initial_locals)
        
        argchecks = sum((check_stmtlist(ast.Name(id=arg.var, ctx=ast.Load()), ty, 'Argument of incorrect type', \
                                            lineno=n.lineno) for (arg, ty) in argtys), [])

        fo = self.falloffvisitor.dispatch_statements(body)
        if nty.to != Dyn and nty.to != Void and fo != WILL_RETURN:
            return error_stmt('Return value of incorrect type', n.lineno)

        if flags.PY_VERSION == 3:
            return [ast.FunctionDef(name=n.name, args=args,
                                     body=argchecks+body, decorator_list=decorator_list,
                                     returns=n.returns, lineno=n.lineno)]
        elif flags.PY_VERSION == 2:
            return [ast.FunctionDef(name=n.name, args=args,
                                     body=argchecks+body, decorator_list=decorator_list,
                                     lineno=n.lineno)]

    def visitarguments(self, n, env, nty, misc):
        if n.vararg:
            warn('Varargs are currently unsupported. Attempting to use them will result in a type error', 3)
        if n.kwarg:
            warn('Keyword args are currently unsupported. Attempting to use them will result in a type error', 3)
        if flags.PY_VERSION == 3 and n.kwonlyargs:
            warn('Keyword args are currently unsupported. Attempting to use them will result in a type error', 3)
        checked_args = nty.froms[-len(n.defaults):]
        defaults = []
        for val, ty in zip(n.defaults, checked_args):
            val, vty = self.dispatch(val, env, misc)
            defaults.append(cast(env, misc.cls, val, vty, ty, 'Default argument of incorrect type'))
        
        args, argns = tuple(zip(*[self.dispatch(arg, env, misc) for arg in n.args])) if\
            len(n.args) > 0 else ([], [])

        args = list(args)
        argns = list(argns)

        if flags.PY_VERSION == 3:
            nargs = ast.arguments(args=args, vararg=None, varargannotation=None, kwonlyargs=[], kwarg=None,
                                  kwargannotation=None, defaults=defaults, kw_defaults=[])
        elif flags.PY_VERSION == 2:
            nargs = ast.arguments(args=args, vararg=None, kwarg=None, defaults=defaults) 
        return nargs, argns

    def visitarg(self, n, env, misc):
        def annotation(n):
            if misc.cls:
                if isinstance(n, ast.Name) and n.id == misc.cls.name:
                    if misc.receiver:
                        return ast.Attribute(value=misc.receiver, attr='__class__', ctx=ast.Load())
                    else: return None
                elif isinstance(n, ast.Attribute):
                    return ast.Attribute(value=attribute(n.value), attr=n.attr, ctx=n.ctx)
            return n
        if flags.PY_VERSION == 3:
            return ast.arg(arg=n.arg, annotation=annotation(n.annotation)), n.arg
        else: return n, n.arg
            
    def visitReturn(self, n, env, misc):
        if n.value:
            value, ty = self.dispatch(n.value, env, misc)
            value = cast(env, misc.cls, value, ty, misc.ret, "Return value of incorrect type")
        else:
            value = None
            if not subcompat(Void, misc.misc):
                return error_stmt('Return value expected', n.lineno)
        return [ast.Return(value=value, lineno=n.lineno)]

    # Assignment stuff
    def visitAssign(self, n, env, misc):
        val, vty = self.dispatch(n.value, env, misc)
        ttys = []
        targets = []
        attrs = []
        for target in n.targets:
            (ntarget, tty) = self.dispatch(target, env, misc)
            if flags.SEMANTICS == 'MONO' and isinstance(target, ast.Attribute) and \
                    not tyinstance(tty, Dyn):
                attrs.append((ntarget, tty))
            else:
                ttys.append(tty)
                targets.append(ntarget)
        stmts = []
        if targets:
            try:
                meet = tymeet(ttys)
            except Bot:
                return error_stmt('Assignee of incorrect type', n.lineno)

            val = cast(env, misc.cls, val, vty, meet, "Assignee of incorrect type")
            stmts.append(ast.Assign(targets=targets, value=val, lineno=n.lineno))
        for target, tty in attrs:
            lval = cast(env, misc.cls, val, vty, tty, 'Assignee of incorrect type')
            stmts.append(ast.Expr(ast.Call(func=ast.Name(id='retic_setattr_'+\
                                                             ('static' if \
                                                                  tty.static() else 'dynamic'), 
                                                         ctx=ast.Load()),
                                           args=[target.value, ast.Str(s=target.attr), lval, tty.to_ast()],
                                           keywords=[], starargs=None, kwargs=None),
                                  lineno=n.lineno))
        return stmts

    def visitAugAssign(self, n, env, misc):
        optarget = utils.copy_assignee(n.target, ast.Load())
        assignment = ast.Assign(targets=[n.target], 
                                value=ast.BinOp(left=optarget,
                                                op=n.op,
                                                right=n.value),
                                lineno=n.lineno)
        
        return self.dispatch(assignment, env, misc)

    def visitDelete(self, n, env, misc):
        targets = []
        for t in n.targets:
            value, ty = self.dispatch(t, env, misc)
            targets.append(utils.copy_assignee(value, ast.Load()))
        return [ast.Expr(targ, lineno=n.lineno) for targ in targets] + \
                    [ast.Delete(targets=n.targets, lineno=n.lineno)]

    # Control flow stuff
    def visitIf(self, n, env, misc):
        test, tty = self.dispatch(n.test, env, misc)
        body = self.dispatch_statements(n.body, env, misc)
        orelse = self.dispatch_statements(n.orelse, env, misc) if n.orelse else []
        return [ast.If(test=test, body=body, orelse=orelse, lineno=n.lineno)]

    def visitFor(self, n, env, misc):
        target, tty = self.dispatch(n.target, env, misc)
        iter, ity = self.dispatch(n.iter, env, misc)
        body = self.dispatch_statements(n.body, env, misc)
        orelse = self.dispatch_statements(n.orelse, env, misc) if n.orelse else []
        
        targcheck = check_stmtlist(utils.copy_assignee(target, ast.Load()),
                                   tty, 'Iterator of incorrect type', lineno=n.lineno)
        return [ast.For(target=target, iter=cast(env, misc.cls, iter, ity, Iterable(tty),
                                                 'iterator list of incorrect type'),
                        body=targcheck+body, orelse=orelse, lineno=n.lineno)]
        
    def visitWhile(self, n, env, misc):
        test, tty = self.dispatch(n.test, env, misc)
        body = self.dispatch_statements(n.body, env, misc)
        orelse = self.dispatch_statements(n.orelse, env, misc) if n.orelse else []
        return [ast.While(test=test, body=body, orelse=orelse, lineno=n.lineno)]

    def visitWith(self, n, env, misc): #2.7, 3.2 -- UNDEFINED FOR 3.3 right now
        context_expr, _ = self.dispatch(n.context_expr, env, misc)
        optional_vars, _ = self.dispatch(n.optional_vars, env, misc) if n.optional_vars else (None, Dyn)
        body = self.dispatch_statements(n.body, env, misc)
        return [ast.With(context_expr=context_expr, optional_vars=optional_vars, body=body, lineno=n.lineno)]
    
    # Class stuff
    def visitClassDef(self, n, env, misc): #Keywords, kwargs, etc
        bases = [self.dispatch(base, env, misc)[0] for base in n.bases]
        if flags.PY_VERSION == 3:
            keywords = []
            metaclass_handled = flags.SEMANTICS != 'MONO'
            for keyword in n.keywords:
                kval, _ = self.dispatch(keyword.value, env, misc)
                if flags.SEMANTICS == 'MONO' and keyword.arg == 'metaclass':
                    metaclass_handled = True
                keywords.append(ast.keyword(arg=keyword.arg, value=kval))
            if not metaclass_handled:
                warn('Adding Monotonic metaclass to classdef at line %s: <%s>' % (n.lineno, n.name), 1)
                keywords.append(ast.keyword(arg='metaclass', 
                                            value=ast.Name(id=Monotonic.__name__,
                                                           ctx=ast.Load())))
        nty = env[Var(n.name)]
        env = env.copy()
        
        initial_locals = {n.name: nty}
        body = self.dispatch_class(n.body, env, Misc(ret=Void, cls=nty, methodscope=True), initial_locals)

        if flags.PY_VERSION == 3:
            return [ast.ClassDef(name=n.name, bases=bases, keywords=keywords,
                                 starargs=n.starargs, kwargs=n.kwargs, body=body,
                                 decorator_list=n.decorator_list, lineno=n.lineno)]
        elif flags.PY_VERSION == 2:
            return [ast.ClassDef(name=n.name, bases=bases, body=body,
                                 decorator_list=n.decorator_list, lineno=n.lineno)]

    # Exception stuff
    # Python 2.7, 3.2
    def visitTryExcept(self, n, env, misc):
        body = self.dispatch_statements(n.body, env, misc)
        handlers = []
        for handler in n.handlers:
            handler = self.dispatch(handler, env, misc)
            handlers.append(handler)
        orelse = self.dispatch(n.orelse, env, misc) if n.orelse else []
        return [ast.TryExcept(body=body, handlers=handlers, orelse=orelse, lineno=n.lineno)]

    # Python 2.7, 3.2
    def visitTryFinally(self, n, env, misc):
        body = self.dispatch_statements(n.body, env, misc)
        finalbody = self.dispatch_statements(n.finalbody, env, misc)
        return [ast.TryFinally(body=body, finalbody=finalbody, lineno=n.lineno)]
    
    # Python 3.3
    def visitTry(self, n, env, misc):
        body = self.dispatch_statements(n.body, env, misc)
        handlers = []
        for handler in n.handlers:
            handler = self.dispatch(handler, env, misc)
            handlers.append(handler)
        orelse = self.dispatch(n.orelse, env, misc) if n.orelse else []
        finalbody = self.dispatch_statements(n.finalbody, env, misc)
        return [ast.Try(body=body, handlers=handlers, orelse=orelse, finalbody=finalbody, lineno=n.lineno)]

    def visitExceptHandler(self, n, env, misc):
        type, tyty = self.dispatch(n.type, env, misc) if n.type else (None, Dyn)
        body = self.dispatch_statements(n.body, env, misc)
        if flags.PY_VERSION == 2 and n.name and type:
            name, nty = self.dispatch(n.name, env, misc)
            type = cast(env, misc.cls, type, tyty, nty, "Incorrect exception type")
        else: 
            name = n.name
        return ast.ExceptHandler(type=type, name=name, body=body, lineno=n.lineno)

    def visitRaise(self, n, env, misc):
        if flags.PY_VERSION == 3:
            exc, _ = self.dispatch(n.exc, env, misc) if n.exc else (None, Dyn)
            cause, _ = self.dispatch(n.cause, env, misc) if n.cause else (None, Dyn)
            return [ast.Raise(exc=exc, cause=cause, lineno=n.lineno)]
        elif flags.PY_VERSION == 2:
            type, _ = self.dispatch(n.type, env, misc) if n.type else (None, Dyn)
            inst, _ = self.dispatch(n.inst, env, misc) if n.inst else (None, Dyn)
            tback, _ = self.dispatch(n.tback, env, misc) if n.tback else (None, Dyn)
            return [ast.Raise(type=type, inst=inst, tback=tback, lineno=n.lineno)]

    def visitAssert(self, n, env, misc):
        test, _ = self.dispatch(n.test, env, misc)
        msg, _ = self.dispatch(n.msg, env, misc) if n.msg else (None, Dyn)
        return [ast.Assert(test=test, msg=msg, lineno=n.lineno)]

    # Declaration stuff
    def visitGlobal(self, n, env, misc):
        return [n]

    def visitNonlocal(self, n, env, misc):
        return [n]

    # Miscellaneous
    def visitExpr(self, n, env, misc):
        value, ty = self.dispatch(n.value, env, misc)
        return [ast.Expr(value=value, lineno=n.lineno)]

    def visitPass(self, n, env, misc):
        return [n]

    def visitBreak(self, n, env, misc):
        return [n]

    def visitContinue(self, n, env, misc):
        return [n]

    def visitPrint(self, n, env, misc):
        dest, _ = self.dispatch(n.dest, env, misc) if n.dest else (None, Void)
        values = [self.dispatch(val, env, misc)[0] for val in n.values]
        return [ast.Print(dest=dest, values=values, nl=n.nl)]

    def visitExec(self, n, env, misc):
        body, _ = self.dispatch(n.body, env, misc)
        globals, _ = self.dispatch(n.globals, env, misc) if n.globals else (None, Void)
        locals, _ = self.dispatch(n.locals, env, misc) if n.locals else (None, Void)
        return [ast.Exec(body=body, globals=globals, locals=locals)]

### EXPRESSIONS ###
    # Op stuff
    def visitBoolOp(self, n, env, misc):
        values = []
        tys = []
        for value in n.values:
            (value, ty) = self.dispatch(value, env, misc)
            values.append(value)
            tys.append(ty)
        ty = tyjoin(tys)
        return (ast.BoolOp(op=n.op, values=values), ty)

    def visitBinOp(self, n, env, misc):
        (left, lty) = self.dispatch(n.left, env, misc)
        (right, rty) = self.dispatch(n.right, env, misc)
        node = ast.BinOp(left=left, op=n.op, right=right)
        try:
            ty = binop_type(lty, n.op, rty)
        except Bot:
            return error('Incompatible types for binary operation'), Dyn
        return (node, ty)

    def visitUnaryOp(self, n, env, misc):
        (operand, ty) = self.dispatch(n.operand, env, misc)
        node = ast.UnaryOp(op=n.op, operand=operand)
        if isinstance(n.op, ast.Invert):
            ty = primjoin([ty], Int, Int)
        elif any([isinstance(n.op, op) for op in [ast.UAdd, ast.USub]]):
            ty = primjoin([ty])
        elif isinstance(n.op, ast.Not):
            ty = Bool
        return (node, ty)

    def visitCompare(self, n, env, misc):
        (left, _) = self.dispatch(n.left, env, misc)
        comparators = [comp for (comp, _) in [self.dispatch(ocomp, env, misc) for ocomp in n.comparators]]
        return (ast.Compare(left=left, ops=n.ops, comparators=comparators), Bool)

    # Collections stuff    
    def visitList(self, n, env, misc):
        eltdata = [self.dispatch(x, env, misc) for x in n.elts]
        elttys = [ty for (elt, ty) in eltdata] 
        elts = [elt for (elt, ty) in eltdata]
        if isinstance(n.ctx, ast.Store):
            try:
                inty = tymeet(elttys)
            except Bot:
                return error(''), Dyn
            ty = Iterable(inty)
        else:
            inty = tyjoin(elttys)
            ty = List(inty)
        return (ast.List(elts=elts, ctx=n.ctx), ty)

    def visitTuple(self, n, env, misc):
        eltdata = [self.dispatch(x, env, misc) for x in n.elts]
        tys = [ty for (elt, ty) in eltdata]
        elts = [elt for (elt, ty) in eltdata]
        if isinstance(n.ctx, ast.Store):
            try:
                ty = Iterable(tymeet(tys))
            except Bot:
                return error(''), Dyn
        else:
            ty = Tuple(*tys)
        return (ast.Tuple(elts=elts, ctx=n.ctx), ty)

    def visitDict(self, n, env, misc):
        keydata = [self.dispatch(key, env, misc) for key in n.keys]
        valdata = [self.dispatch(val, env, misc) for val in n.values]
        keys, ktys = list(zip(*keydata)) if keydata else ([], [])
        values, vtys = list(zip(*valdata)) if valdata else ([], [])
        return (ast.Dict(keys=list(keys), values=list(values)), Dict(tyjoin(list(ktys)), tyjoin(list(vtys))))

    def visitSet(self, n, env, misc):
        eltdata = [self.dispatch(x, env, misc) for x in n.elts]
        elttys = [ty for (elt, ty) in eltdata]
        ty = tyjoin(elttys)
        elts = [elt for (elt, ty) in eltdata]
        return (ast.Set(elts=elts), Set(ty))

    def visitListComp(self, n, env, misc):
        generators = [self.dispatch(generator, env, misc) for generator in n.generators]
        elt, ety = self.dispatch(n.elt, env, misc)
        return check(ast.ListComp(elt=elt, generators=generators), List(ety), 'List comprehension of incorrect type', lineno=n.lineno), List(ety)

    def visitSetComp(self, n, env, misc):
        generators = [self.dispatch(generator, env, misc) for generator in n.generators]
        elt, ety = self.dispatch(n.elt, env, misc)
        return check(ast.SetComp(elt=elt, generators=generators), Set(ety), 'Set comprehension of incorrect type', lineno=n.lineno), Set(ety)

    def visitDictComp(self, n, env, misc):
        generators = [self.dispatch(generator, env, misc) for generator in n.generators]
        key, kty = self.dispatch(n.key, env, misc)
        value, vty = self.dispatch(n.value, env, misc)
        return check(ast.DictComp(key=key, value=value, generators=generators), Dict(kty, vty), 'Dict comprehension of incorrect type', lineno=n.lineno), Dict(kty, vty)

    def visitGeneratorExp(self, n, env, misc):
        generators = [self.dispatch(generator, env, misc) for generator in n.generators]
        elt, ety = self.dispatch(n.elt, env, misc)
        return check(ast.GeneratorExp(elt=elt, generators=generators), Iterable(ety), 'Comprehension of incorrect type', lineno=n.lineno), Iterable(ety)

    def visitcomprehension(self, n, env, misc):
        (iter, ity) = self.dispatch(n.iter, env, misc)
        ifs = [if_ for (if_, _) in [self.dispatch(if2, env, misc) for if2 in n.ifs]]
        (target, tty) = self.dispatch(n.target, env, misc)
        return ast.comprehension(target=target, iter=cast(env, misc.cls, iter, ity, Iterable(tty), 'Iterator list of incorrect type'), ifs=ifs)

    # Control flow stuff
    def visitYield(self, n, env, misc):
        value, _ = self.dispatch(n.value, env, misc) if n.value else (None, Void)
        return ast.Yield(value=value), Dyn

    def visitYieldFrom(self, n, env, misc):
        value, _ = self.dispatch(n.value, env, misc)
        return ast.YieldFrom(value=value), Dyn

    def visitIfExp(self, n, env, misc):
        test, _ = self.dispatch(n.test, env, misc)
        body, bty = self.dispatch(n.body, env, misc)
        orelse, ety = self.dispatch(n.orelse, env, misc)
        return ast.IfExp(test=test, body=body, orelse=orelse), tyjoin([bty,ety])

    # Function stuff
    def visitCall(self, n, env, misc):
        class BadCall(Exception):
            def __init__(self, msg):
                self.msg = msg
        def cast_args(argdata, fun, funty):
            vs, ss = zip(*argdata) if argdata else ([], [])
            vs = list(vs)
            ss = list(ss)
            if tyinstance(funty, Dyn):
                return vs, cast(env, misc.cls, fun, Dyn, Function(ss, Dyn),
                                'Function of incorrect type'), Dyn
            elif tyinstance(funty, Function):
                if len(argdata) == len(funty.froms):
                    return ([cast(env, misc.cls, v, s, t, 'Argument of incorrect type') for \
                                (v, s), t in zip(argdata, funty.froms)],
                            fun, funty.to)
                else: 
                    raise BadCall('Incorrect number of arguments')
            elif tyinstance(funty, Class):
                if '__init__' in funty.members:
                    inst = funty.instance()
                    funty = funty.member_type('__init__')
                    if tyinstance(funty, Function):
                        funty = funty.bind()
                        funty.to = inst
                else:
                    funty = Function([], funty.instance())
                return cast_args(argdata, fun, funty)
            else: raise BadCall('Uncallable object called')

        (func, ty) = self.dispatch(n.func, env, misc)
        argdata = [self.dispatch(x, env, misc) for x in n.args]
        try:
            (args, func, retty) = cast_args(argdata, func, ty)
        except BadCall as e:
            return error(e.msg)
        call = ast.Call(func=func, args=args, keywords=n.keywords,
                        starargs=n.starargs, kwargs=n.kwargs)
        call = check(call, retty, "Return value of incorrect type", lineno=n.lineno)
        return (call, retty)

    def visitLambda(self, n, env, misc):
        args, argnames = self.dispatch(n.args, env, misc)
        params = [Dyn] * len(argnames)
        env = env.copy()
        env.update(dict(list(zip(argnames, params))))
        body, rty = self.dispatch(n.body, env, misc)
        return ast.Lambda(args=args, body=body), Function(params, rty)

    # Variable stuff
    def visitName(self, n, env, misc):
        if isinstance(n.ctx, ast.Param): # Compatibility with 2.7
            return n.id
        try:
            ty = env[Var(n.id)]
            if isinstance(n.ctx, ast.Del) and not tyinstance(ty, Dyn):
                return error('Attempting to delete statically typed id'), ty
        except KeyError:
            ty = Dyn
        return (n, ty)

    def visitAttribute(self, n, env, misc):
        value, vty = self.dispatch(n.value, env, misc)

        if hasattr(vty, 'structure'):
            vty = vty.structure()

        if tyinstance(vty, Self):
            if isinstance(n.ctx, ast.Store):
                return error('Attempting to write to attribute of self-typed argument')
            if not misc.cls:
                return error('Attempting to use self-type in non-class context')
            if not misc.receiver:
                return error('Attempting to use self-type in non-method context')
            ty = misc.cls.instance().member_type(n.attr)
            return ast.Call(func=ast.Name(id='retic_bindmethod', ctx=ast.Load()),
                            args=[ast.Attribute(value=misc.receiver, attr='__class__', ctx=ast.Load()),
                                  n.value, ast.Str(s=n.attr)], keywords=[], starargs=None, kwargs=None), \
                                  ty
        elif tyinstance(vty, Object) or tyinstance(vty, Class):
            try:
                ty = vty.member_type(n.attr)
                if isinstance(n.ctx, ast.Del):
                    return error('Attempting to delete statically typed attribute'), ty
            except KeyError:
                if not isinstance(n.ctx, ast.Store):
                    value = cast(env, misc.cls, value, vty, Object('', {n.attr: Dyn}), 
                                 'Attempting to access nonexistant attribute')
                ty = Dyn
        elif tyinstance(vty, Dyn):
            if not isinstance(n.ctx, ast.Store) and not isinstance(n.ctx, ast.Del):
                value = cast(env, misc.cls, value, vty, Record({n.attr: Dyn}), 
                             'Attempting to access nonexistant attribute') 
            else:
                value = cast(env, misc.cls, value, vty, Record({}), 
                             'Attempting to %s non-object' % ('write to' if isinstance(n.ctx, ast.Store) \
                                                                  else 'delete from') )
            ty = Dyn
        else: return error('Attempting to access from object of type %s (line %d)' % (vty, n.lineno)), Dyn

        if flags.SEMANTICS == 'MONO' and not isinstance(n.ctx, ast.Store) and not isinstance(n.ctx, ast.Del) and \
                not tyinstance(ty, Dyn):
            ans = ast.Call(func=ast.Name(id='retic_getattr_'+('static' if ty.static() else 'dynamic'), 
                                         ctx=ast.Load()),
                           args=[value, ast.Str(s=n.attr), ty.to_ast()],
                        keywords=[], starargs=None, kwargs=None)
            return ans, ty

        ans = ast.Attribute(value=value, attr=n.attr, ctx=n.ctx)
        if not isinstance(n.ctx, ast.Store) and not isinstance(n.ctx, ast.Del):
            ans = check(ans, ty, 'Value of incorrect type in object')
        return ans, ty

    def visitSubscript(self, n, env, misc):
        value, vty = self.dispatch(n.value, env, misc)
        slice, ty = self.dispatch(n.slice, env, vty, misc, n.lineno)
        ans = ast.Subscript(value=value, slice=slice, ctx=n.ctx)
        if not isinstance(n.ctx, ast.Store):
            ans = check(ans, ty, 'Value of incorrect type in subscriptable', lineno=n.lineno)
        return ans, ty

    def visitIndex(self, n, env, extty, misc, lineno):
        value, vty = self.dispatch(n.value, env, misc)
        if tyinstance(extty, List):
            value = cast(env, misc.cls, value, vty, Int, 'Indexing with non-integer type')
            ty = extty.type
        elif tyinstance(extty, String):
            value = cast(env, misc.cls, value, vty, Int, 'Indexing with non-integer type')
            ty = String
        elif tyinstance(extty, Tuple):
            value = cast(env, misc.cls, value, vty, Int, 'Indexing with non-integer type')
            ty = Dyn
        elif tyinstance(extty, Dict):
            value = cast(env, misc.cls, value, vty, extty.keys, 'Indexing dict with non-key value')
            ty = extty.values
        elif tyinstance(extty, Object):
            # Expand
            ty = Dyn
        elif tyinstance(extty, Class):
            # Expand
            ty = Dyn
        elif tyinstance(extty, Dyn):
            ty = Dyn
        else: 
            return error('Attmepting to index non-indexable value of type %s (line %d)' % (extty, lineno)), Dyn
        # More cases...?
        return ast.Index(value=value), ty

    def visitSlice(self, n, env, extty, misc, lineno):
        lower, lty = self.dispatch(n.lower, env, misc) if n.lower else (None, Void)
        upper, uty = self.dispatch(n.upper, env, misc) if n.upper else (None, Void)
        step, sty = self.dispatch(n.step, env, misc) if n.step else (None, Void)
        if tyinstance(extty, List):
            lower = cast(env, misc.cls, lower, vty, Int, 'Indexing with non-integer type') if lty != Void else lower
            upper = cast(env, misc.cls, upper, vty, Int, 'Indexing with non-integer type') if uty != Void else upper
            step = cast(env, misc.cls, step, vty, Int, 'Indexing with non-integer type') if sty != Void else step
            ty = extty
        elif tyinstance(extty, Object) or tyinstance(extty, Class):
            # Expand
            ty = Dyn
        elif tyinstance(extty, Dyn):
            ty = Dyn
        else: 
            return error('Attempting to slice non-sliceable value of type %s (line %d)' % (extty, lineno)), Dyn
        return ast.Slice(lower=lower, upper=upper, step=step), ty

    def visitExtSlice(self, n, env, extty, misc, lineno):
        dims = [dim for (dim, _) in [self.dispatch(dim2, n, env, extty, misc) for dim2 in n.dims]]
        return ast.ExtSlice(dims=dims), Dyn

    def visitEllipsis(self, n, env, *args): 
        #Yes, this looks stupid, but Ellipses are different kinds of things in Python 2 and 3 and if we ever
        #support them meaningfully this distinction will be crucial
        if flags.PY_VERSION == 2: 
            extty = args[0]
            return (n, Dyn)
        elif flags.PY_VERSION == 3:
            return (n, Dyn)

    def visitStarred(self, n, env, misc):
        value, _ = self.dispatch(n.value, env, misc)
        return ast.Starred(value=value, ctx=n.ctx), Dyn

    # Literal stuff
    def visitNum(self, n, env, misc):
        ty = Dyn
        v = n.n
        if type(v) == int or (flags.PY_VERSION == 2 and type(v) == long):
            ty = Int
        elif type(v) == float:
            ty = Float
        elif type(v) == complex:
            ty = Complex
        return (n, ty)

    def visitStr(self, n, env, misc):
        return (n, String)
    def visitBytes(self, n, env, misc):
        return (n, Dyn)
