from __future__ import print_function
import ast
from vis import Visitor
from gatherers import FallOffVisitor, WILL_RETURN
from typefinder import Typefinder, aliases
from inference import InferVisitor
from typing import *
from relations import *
from exc import StaticTypeError, UnimplementedException
from errors import errmsg, static_val
from astor.misc import get_binop
import typing, ast, utils, flags, rtypes

def fixup(n, lineno=None, col_offset=None):
    if isinstance(n, list) or isinstance(n, tuple):
        return [fixup(e, lineno if lineno else e.lineno) for e in n]
    else:
        if lineno != None:
            n.lineno = lineno
        if col_offset != None:
            n.col_offset = None
        return ast.fix_missing_locations(n)

class Misc(object):
    ret = Void
    cls = None
    receiver = None
    methodscope = False
    extenv = {}
    def __init__(self, **kwargs):
        self.ret = kwargs.get('ret', Void)
        self.cls = kwargs.get('cls', None)
        self.receiver = kwargs.get('receiver', None)
        self.methodscope = kwargs.get('methodscope', False)
        self.extenv = kwargs.get('extenv', {})

##Cast insertion functions##
#Normal casts
def cast(env, ctx, val, src, trg, msg, cast_function='retic_cast'):
    if flags.SEMI_DRY:
        return val
    if flags.SQUELCH_MESSAGES:
        msg = ''
    assert hasattr(val, 'lineno'), ast.dump(val)
    lineno = str(val.lineno)
    merged = merge(src, trg)
    if not subcompat(src, trg, env, ctx):
        return error(msg % static_val(src), lineno)
    elif src == merged:
        return val
    elif not flags.OPTIMIZED_INSERTION:
        warn('Inserting cast at line %s: %s => %s' % (lineno, src, trg), 2)
        return fixup(ast.Call(func=ast.Name(id=cast_function, ctx=ast.Load()),
                              args=[val, src.to_ast(), merged.to_ast(), ast.Str(s=msg)],
                              keywords=[], starargs=None, kwargs=None), val.lineno)
    else:
        if flags.SEMANTICS == 'MONO':
            warn('Inserting cast at line %s: %s => %s' % (lineno, src, trg), 2)
            return fixup(ast.Call(func=ast.Name(id=cast_function, ctx=ast.Load()),
                                  args=[val, src.to_ast(), merged.to_ast(), ast.Str(s=msg)],
                                  keywords=[], starargs=None, kwargs=None), val.lineno)
        elif flags.SEMANTICS == 'TRANS':
            warn('Inserting cast at line %s: %s => %s' % (lineno, src, trg), 2)
            return fixup(ast.Call(func=ast.Name(id=cast_function, ctx=ast.Load()),
                                  args=[val, src.to_ast(), merged.to_ast(), ast.Str(s=msg)],
                                  keywords=[], starargs=None, kwargs=None), val.lineno)
        elif flags.SEMANTICS == 'GUARDED':
            warn('Inserting cast at line %s: %s => %s' % (lineno, src, trg), 2)
            return fixup(ast.Call(func=ast.Name(id=cast_function, ctx=ast.Load()),
                                  args=[val, src.to_ast(), merged.to_ast(), ast.Str(s=msg)],
                                  keywords=[], starargs=None, kwargs=None), val.lineno)
        else: raise UnimplementedException('Efficient insertion unimplemented for this semantics')

# Casting with unknown source type, as in cast-as-assertion 
# function return values at call site
def check(val, trg, msg, check_function='retic_check', lineno=None):
    if flags.SEMI_DRY:
        return val
    if flags.SQUELCH_MESSAGES:
        msg = ''
    assert hasattr(val, 'lineno')
    lineno = str(val.lineno)

    if not flags.OPTIMIZED_INSERTION:
        warn('Inserting check at line %s: %s' % (lineno, trg), 2)
        return fixup(ast.Call(func=ast.Name(id=check_function, ctx=ast.Load()),
                              args=[val, trg.to_ast(), ast.Str(s=msg)],
                              keywords=[], starargs=None, kwargs=None), val.lineno)
    else:
        if flags.SEMANTICS == 'TRANS':
            if not tyinstance(trg, Dyn):
                warn('Inserting check at line %s: %s' % (lineno, trg), 2)
                return fixup(ast.Call(func=ast.Name(id=check_function, ctx=ast.Load()),
                                      args=[val, trg.to_ast(), ast.Str(s=msg)],
                                      keywords=[], starargs=None, kwargs=None), val.lineno)
            else: return val
        else: return val

# Check, but within an expression statement
def check_stmtlist(val, trg, msg, check_function='retic_check', lineno=None):
    if flags.SEMI_DRY:
        return []
    assert hasattr(val, 'lineno'), ast.dump(val)
    chkval = check(val, trg, msg, check_function, val.lineno)
    if not flags.OPTIMIZED_INSERTION:
        return [ast.Expr(value=chkval, lineno=val.lineno)]
    else:
        if flags.SEMANTICS != 'TRANS' or chkval == val or tyinstance(trg, Dyn):
            return []
        else: return [ast.Expr(value=chkval, lineno=val.lineno)]

# Insert a call to an error function if we've turned off static errors
def error(msg, lineno, error_function='retic_error'):
    if flags.STATIC_ERRORS or flags.SEMI_DRY:
        raise StaticTypeError(msg)
    else:
        warn('Static error detected at line %d' % lineno, 0)
        return fixup(ast.Call(func=ast.Name(id=error_function, ctx=ast.Load()),
                              args=[ast.Str(s=msg+' (statically detected)')], keywords=[], starargs=None,
                              kwargs=None), lineno)

# Error, but within an expression statement
def error_stmt(msg, lineno, error_function='retic_error'):
    if flags.STATIC_ERRORS or flags.SEMI_DRY:
        raise StaticTypeError(msg)
    else:
        return [ast.Expr(value=error(msg, lineno, error_function), lineno=lineno)]

def conditional(val, trg, rest, msg, check_function='retic_check', lineno=None):
    if flags.SEMI_DRY:
        return rest
    assert hasattr(val, 'lineno'), ast.dump(val)
    chkval = check(val, trg, msg, check_function, val.lineno)
    cond = ast.IfExp(test=chkval, body=rest, orelse=rest)
    if not flags.OPTIMIZED_INSERTION:
        return cond
    else:
        if flags.SEMANTICS != 'TRANS' or chkval == val or tyinstance(trg, Dyn):
            return rest
        else: return cond

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
            print(ast.dump(ret))
        return ret

    if flags.DEBUG_VISITOR:
        dispatch = dispatch_debug

    def typecheck(self, n, filename, depth, initial_environment=None):
        if initial_environment is None:
            initial_environment = {}
        else: initial_environment = initial_environment.copy()
        self.filename = filename
        self.depth = depth
        n = ast.fix_missing_locations(n)
        typing.debug('Typecheck starting for %s' % filename, [flags.ENTRY, flags.PROC])
        initial_environment.update(typing.initial_environment())
        tn, env = self.preorder(n, initial_environment)
        typing.debug('Typecheck finished for %s' % filename, flags.PROC)
        tn = ast.fix_missing_locations(tn)
        if flags.DRY_RUN:
            return n, env
        return tn, env

    def dispatch_scope(self, n, env, misc, initial_locals=None):
        if initial_locals == None:
            initial_locals = {}
        env = env.copy()
        try:
            typing.debug('Typefinding starting in %s' % self.filename, flags.PROC)
            uenv, locals = self.typefinder.dispatch_scope(n, env, initial_locals, self.depth, 
                                                          self.filename,type_inference=True)
            typing.debug('Typefinding finished in %s' % self.filename, flags.PROC)
        except StaticTypeError as exc:
            if flags.STATIC_ERRORS:
                raise exc
            else:
                return error_stmt(exc.args[0], n[0].lineno if len(n) > 0 else -1), env 
        env.update(uenv)
        locals = locals.keys()
        self.infervisitor.filename = self.filename
        typing.debug('Inference starting in %s' % self.filename, flags.PROC)
        env = self.infervisitor.infer(self, locals, initial_locals, n, env, misc)
        typing.debug('Inference finished in %s' % self.filename, flags.PROC)
        body = []
        for s in n:
            stmts = self.dispatch(s, env, misc)
            body += stmts
        return body, env

    def dispatch_class(self, n, env, misc, initial_locals=None):
        if initial_locals == None:
            initial_locals = {}
        env = env.copy()
        try:
            typing.debug('Typefinding (for class) starting in %s' % self.filename, flags.PROC)
            uenv, _ = self.typefinder.dispatch_scope(n, env, initial_locals, self.depth, self.filename,
                                                     tyenv=aliases(env), type_inference=False)
            typing.debug('Typefinding (for class) starting in %s' % self.filename, flags.PROC)
        except StaticTypeError as exc:
            if flags.STATIC_ERRORS:
                raise exc
            else:
                return error_stmt(exc.args[0], n[0].lineno if len(n) > 0 else -1)
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

        try:
            nty = env[Var(n.name)]
        except KeyError as e :
            assert False, ('%s at %s:%d' % (e ,self.filename, n.lineno))

        name = n.name if n.name not in rtypes.TYPES else n.name + '_'
        assign = ast.Assign(targets=[ast.Name(id=name, ctx=ast.Store(), lineno=n.lineno)], 
                            value=cast(env, misc.cls, ast.Name(id=name, ctx=ast.Load(), lineno=n.lineno), Dyn, nty, errmsg('BAD_FUNCTION_INJECTION', self.filename, n, nty)))

        froms = nty.froms if hasattr(nty, 'froms') else DynParameters#[Dyn] * len(argnames)
        to = nty.to if hasattr(nty, 'to') else Dyn

        args, argnames, specials = self.dispatch(n.args, env, froms, misc, n.lineno)
        decorator_list = n.decorator_list#[self.dispatch(dec, env, misc)[0] for dec in n.decorator_list if not is_annotation(dec)]
        # Decorators have a restricted syntax that doesn't allow function calls
        env = (misc.extenv if misc.cls else env).copy()

        if misc.cls:
            receiver = None if (not misc.methodscope or len(argnames) == 0) else\
                ast.Name(id=argnames[0], ctx=ast.Load())
        else: 
            receiver = None


        argtys = froms.lenmatch([Var(x) for x in argnames])
        assert(argtys != None)
        initial_locals = dict(argtys + specials)
        print(initial_locals)
        typing.debug('Function %s typechecker starting in %s' % (n.name, self.filename), flags.PROC)
        body, _ = self.dispatch_scope(n.body, env, Misc(ret=to, cls=misc.cls, receiver=receiver, extenv=misc.extenv), 
                                   initial_locals)
        typing.debug('Function %s typechecker finished in %s' % (n.name, self.filename), flags.PROC)
        
        force_checks = tyinstance(froms, DynParameters)

        argchecks = sum((check_stmtlist(ast.Name(id=arg.var, ctx=ast.Load(), lineno=n.lineno), ty, 
                                        errmsg('ARG_CHECK', self.filename, n, arg.var, ty), \
                                            lineno=n.lineno) for (arg, ty) in argtys), [])

        typing.debug('Returns checker starting in %s' % self.filename, flags.PROC)
        fo = self.falloffvisitor.dispatch_statements(body)
        typing.debug('Returns checker finished in %s' % self.filename, flags.PROC)
        if to != Dyn and to != Void and fo != WILL_RETURN:
            return error_stmt(errmsg('FALLOFF', self.filename, n, n.name, to), n.lineno)

        if flags.PY_VERSION == 3:
            return [ast.FunctionDef(name=name, args=args,
                                     body=argchecks+body, decorator_list=decorator_list,
                                     returns=n.returns, lineno=n.lineno), assign]
        elif flags.PY_VERSION == 2:
            return [ast.FunctionDef(name=name, args=args,
                                     body=argchecks+body, decorator_list=decorator_list,
                                     lineno=n.lineno), assign]

    def visitarguments(self, n, env, nparams, misc, lineno):
        def argextract(arg):
            if flags.PY_VERSION == 3 and flags.PY3_VERSION >= 4:
                return arg.arg
            else: return arg
        specials = []
        if n.vararg:
            specials.append(Var(argextract(n.vararg)))
        if n.kwarg:
            specials.append(Var(argextract(n.kwarg)))
        if flags.PY_VERSION == 3 and n.kwonlyargs:
            specials += [Var(arg.arg) for arg in n.kwonlyargs]
        
        checked_args = nparams.lenmatch(n.args)
        assert checked_args != None, '%s <> %s, %s, %d' % (nparams, ast.dump(n), self.filename, lineno)
        checked_args = checked_args[-len(n.defaults):]

        defaults = []
        for val, (k, ty) in zip(n.defaults, checked_args):
            val, vty = self.dispatch(val, env, misc)
            defaults.append(cast(env, misc.cls, val, vty, ty, errmsg('DEFAULT_MISMATCH', self.filename, lineno, k, ty)))
        args, argns = tuple(zip(*[self.visitarg(arg, env, misc) for arg in n.args])) if\
            len(n.args) > 0 else ([], [])

        args = list(args)
        argns = list(argns)

        assert len(defaults) == len(n.defaults)

        if flags.PY_VERSION == 3:
            kw_defaults = [(fixup(self.dispatch(d, env, misc)[0], lineno) if d else None) for d in n.kw_defaults]

            nargs = dict(args=args, vararg=n.vararg,
                         kwonlyargs=n.kwonlyargs, kwarg=n.kwarg,
                         defaults=defaults, kw_defaults=kw_defaults)

            if flags.PY3_VERSION < 4:
                nargs['kwargannotation'] = None
                nargs['varargannotation'] = n.varargannotation
        elif flags.PY_VERSION == 2:
            nargs = dict(args=args, vararg=n.vararg, kwarg=None, defaults=defaults) 
        return ast.arguments(**nargs), argns, [(k, Dyn) for k in specials]

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
        else: return n, n.id
            
    def visitReturn(self, n, env, misc):
        if n.value:
            value, ty = self.dispatch(n.value, env, misc)
            value = cast(env, misc.cls, value, ty, misc.ret, errmsg('RETURN_ERROR', self.filename, n, misc.ret))
        else:
            value = None
            if not subcompat(Void, misc.ret):
                return error_stmt(errmsg('RETURN_NONEXISTANT', self.filename, n, misc.ret))
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
            meet = n_info_join(ttys)
            if len(targets) > 1:
                err = errmsg('SINGLE_ASSIGN_ERROR', self.filename, n, meet)
            else:
                err = errmsg('MULTI_ASSIGN_ERROR', self.filename, n, ttys)
            val = cast(env, misc.cls, val, vty, meet, err)
            stmts.append(ast.Assign(targets=targets, value=val, lineno=n.lineno))
        for target, tty in attrs:
            lval = cast(env, misc.cls, val, vty, tty, errmsg('SINGLE_ASSIGN_ERROR', self.filename, n, tty))
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
                                                right=n.value,
                                                lineno=n.lineno),
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
                                   tty, errmsg('ITER_CHECK', self.filename, n, tty), lineno=n.lineno)
        if tyinstance(ity, List):
            iter_ty = List(tty)
        elif tyinstance(ity, Dict):
            iter_ty = Dict(tty, ity.values)
        elif tyinstance(ity, Tuple):
            iter_ty = Tuple(*([tty] * len(ity.elements)))
        else: iter_ty = Dyn
        return [ast.For(target=target, iter=cast(env, misc.cls, iter, ity, iter_ty,
                                                 errmsg('ITER_ERROR', self.filename, n, iter_ty)),
                        body=targcheck+body, orelse=orelse, lineno=n.lineno)]
        
    def visitWhile(self, n, env, misc):
        test, tty = self.dispatch(n.test, env, misc)
        body = self.dispatch_statements(n.body, env, misc)
        orelse = self.dispatch_statements(n.orelse, env, misc) if n.orelse else []
        return [ast.While(test=test, body=body, orelse=orelse, lineno=n.lineno)]

    def visitWith(self, n, env, misc):
        body = self.dispatch_statements(n.body, env, misc)
        if flags.PY_VERSION == 3 and flags.PY3_VERSION >= 3:
            items = [self.dispatch(item, env, misc) for item in n.items]
            return [ast.With(items=items, body=body, lineno=n.lineno)]
        else:
            context_expr, _ = self.dispatch(n.context_expr, env, misc)
            optional_vars, _ = self.dispatch(n.optional_vars, env, misc) if n.optional_vars else (None, Dyn)
            return [ast.With(context_expr=context_expr, optional_vars=optional_vars, body=body, lineno=n.lineno)]
    
    def visitwithitem(self, n, env, misc):
        context_expr, _ = self.dispatch(n.context_expr, env, misc)
        optional_vars, _ = self.dispatch(n.optional_vars, env, misc) if n.optional_vars else (None, Dyn)
        return ast.withitem(context_expr=context_expr, optional_vars=optional_vars)
        

    # Class stuff
    def visitClassDef(self, n, env, misc): #Keywords, kwargs, etc
        bases = [ast.Call(func=ast.Name(id='retic_actual', ctx=ast.Load()), args=[base], kwargs=None, starargs=None, keywords=[]) for base in [self.dispatch(base, env, misc)[0] for base in n.bases]]
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
        oenv = misc.extenv if misc.cls else env.copy()
        env = env.copy()
        
        initial_locals = {n.name: nty}

        stype = ast.Assign(targets=[ast.Name(id='retic_class_type', ctx=ast.Store(), lineno=n.lineno)],
                           value=nty.to_ast())

        typing.debug('Class %s typechecker starting in %s' % (n.name, self.filename), flags.PROC)
        body = [stype] + self.dispatch_class(n.body, env, Misc(ret=Void, cls=nty, methodscope=True, extenv=oenv), initial_locals)
        typing.debug('Class %s typechecker finished in %s' % (n.name, self.filename), flags.PROC)

        name = n.name if n.name not in rtypes.TYPES else n.name + '_'

        assign = ast.Assign(targets=[ast.Name(id=name, ctx=ast.Store(), lineno=n.lineno)], 
                            value=cast(env, misc.cls, ast.Name(id=name, ctx=ast.Load(), lineno=n.lineno), Dyn, nty, 
                                       errmsg('BAD_CLASS_INJECTION', self.filename, n, nty)))

        if flags.PY_VERSION == 3:
            return [ast.ClassDef(name=name, bases=bases, keywords=keywords,
                                 starargs=n.starargs, kwargs=n.kwargs, body=body,
                                 decorator_list=n.decorator_list, lineno=n.lineno), assign]
        elif flags.PY_VERSION == 2:
            return [ast.ClassDef(name=name, bases=bases, body=body,
                                 decorator_list=n.decorator_list, lineno=n.lineno)]

    # Exception stuff
    # Python 2.7, 3.2
    def visitTryExcept(self, n, env, misc):
        body = self.dispatch_statements(n.body, env, misc)
        handlers = []
        for handler in n.handlers:
            handler = self.dispatch(handler, env, misc)
            handlers.append(handler)
        orelse = self.dispatch_statements(n.orelse, env, misc) if n.orelse else []
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
        orelse = self.dispatch_statements(n.orelse, env, misc) if n.orelse else []
        finalbody = self.dispatch_statements(n.finalbody, env, misc)
        return [ast.Try(body=body, handlers=handlers, orelse=orelse, finalbody=finalbody, lineno=n.lineno)]

    def visitExceptHandler(self, n, env, misc):
        type, tyty = self.dispatch(n.type, env, misc) if n.type else (None, Dyn)
        body = self.dispatch_statements(n.body, env, misc)
        if flags.PY_VERSION == 2 and n.name and type:
            name, nty = self.dispatch(n.name, env, misc)
            type = cast(env, misc.cls, type, tyty, nty, errmsg('EXCEPTION_ERROR', self.filename, n, n.name, nty, n.name))
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
        return [ast.Print(dest=dest, values=values, nl=n.nl, lineno=n.lineno)]

    def visitExec(self, n, env, misc):
        body, _ = self.dispatch(n.body, env, misc)
        globals, _ = self.dispatch(n.globals, env, misc) if n.globals else (None, Void)
        locals, _ = self.dispatch(n.locals, env, misc) if n.locals else (None, Void)
        return [ast.Exec(body=body, globals=globals, locals=locals, lineno=n.lineno)]

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
        return (ast.BoolOp(op=n.op, values=values, lineno=n.lineno), ty)

    def visitBinOp(self, n, env, misc):
        if self.filename == 'stats.py':
            print('`BO')
        (left, lty) = self.dispatch(n.left, env, misc)
        (right, rty) = self.dispatch(n.right, env, misc)
        ty = binop_type(lty, n.op, rty)
        if not ty.top_free():
            return error(errmsg('BINOP_INCOMPAT', self.filename, n, lty, rty, get_binop(n.op))), Dyn
        node = ast.BinOp(left=left, op=n.op, right=right, lineno=n.lineno)
        return (node, ty)

    def visitUnaryOp(self, n, env, misc):
        (operand, ty) = self.dispatch(n.operand, env, misc)
        node = ast.UnaryOp(op=n.op, operand=operand, lineno=n.lineno)
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
        return (ast.Compare(left=left, ops=n.ops, comparators=comparators, lineno=n.lineno), Bool)

    # Collections stuff    
    def visitList(self, n, env, misc):
        eltdata = [self.dispatch(x, env, misc) for x in n.elts]
        elttys = [ty for (elt, ty) in eltdata] 
        elts = [elt for (elt, ty) in eltdata]
        if isinstance(n.ctx, ast.Store):
            inty = n_info_join(elttys)
            if not inty.top_free():
                return error(errmsg('LIST_STORE_TARGET', self.filename, n, elttys)), Dyn
            ty = List(inty)
        else:
            inty = tyjoin(elttys)
            ty = List(inty) if flags.TYPED_LITERALS else Dyn
        return ast.List(elts=elts, ctx=n.ctx, lineno=n.lineno), ty

    def visitTuple(self, n, env, misc):
        eltdata = [self.dispatch(x, env, misc) for x in n.elts]
        tys = [ty for (elt, ty) in eltdata]
        elts = [elt for (elt, ty) in eltdata]
        if isinstance(n.ctx, ast.Store):
            ty = Tuple(*tys)
        else:
            ty = Tuple(*tys) if flags.TYPED_LITERALS else Dyn
        return (ast.Tuple(elts=elts, ctx=n.ctx, lineno=n.lineno), ty)

    def visitDict(self, n, env, misc):
        keydata = [self.dispatch(key, env, misc) for key in n.keys]
        valdata = [self.dispatch(val, env, misc) for val in n.values]
        keys, ktys = list(zip(*keydata)) if keydata else ([], [])
        values, vtys = list(zip(*valdata)) if valdata else ([], [])
        return (ast.Dict(keys=list(keys), values=list(values), lineno=n.lineno),\
                    Dict(tyjoin(list(ktys)), tyjoin(list(vtys))))

    def visitSet(self, n, env, misc):
        eltdata = [self.dispatch(x, env, misc) for x in n.elts]
        elttys = [ty for (elt, ty) in eltdata]
        ty = tyjoin(elttys)
        elts = [elt for (elt, ty) in eltdata]
        
        return (ast.Set(elts=elts, lineno=n.lineno), Set(ty) if flags.TYPED_LITERALS else Dyn)

    def visitListComp(self, n, env, misc):
        disp = [self.dispatch(generator, env, misc, n.lineno) for generator in n.generators]
        generators, genenv = zip(*disp) if disp else ([], [])
        lenv = env.copy()
        lenv.update(dict(sum(genenv, [])))
        elt, ety = self.dispatch(n.elt, lenv, misc)
        return check(ast.ListComp(elt=elt, generators=list(generators), lineno=n.lineno), List(ety), errmsg('COMP_CHECK', self.filename, n, List(ety))),\
            (List(ety) if flags.TYPED_LITERALS else Dyn)

    def visitSetComp(self, n, env, misc):
        disp = [self.dispatch(generator, env, misc, n.lineno) for generator in n.generators]
        generators, genenv = zip(*disp) if disp else ([], [])
        lenv = env.copy()
        lenv.update(dict(sum(genenv, [])))
        elt, ety = self.dispatch(n.elt, lenv, misc)
        return check(ast.SetComp(elt=elt, generators=list(generators), lineno=n.lineno), Set(ety), errmsg('COMP_CHECK', self.filename, n, Set(ety))), \
            (Set(ety) if flags.TYPED_LITERALS else Dyn)
    
    def visitDictComp(self, n, env, misc):
        disp = [self.dispatch(generator, env, misc, n.lineno) for generator in n.generators]
        generators, genenv = zip(*disp) if disp else ([], [])
        lenv = env.copy()
        lenv.update(dict(sum(genenv,[])))
        key, kty = self.dispatch(n.key, lenv, misc)
        value, vty = self.dispatch(n.value, lenv, misc)
        return check(ast.DictComp(key=key, value=value, generators=list(generators), lineno=n.lineno), Dict(kty, vty), errmsg('COMP_CHECK', self.filename, n, Dict(kty, vty))), \
            (Dict(kty, vty) if flags.TYPED_LITERALS else Dyn)

    def visitGeneratorExp(self, n, env, misc):
        disp = [self.dispatch(generator, env, misc, n.lineno) for generator in n.generators]
        generators, genenv = zip(*disp) if disp else ([], [])
        lenv = env.copy()
        lenv.update(dict(sum(genenv, [])))
        elt, ety = self.dispatch(n.elt, lenv, misc)
        return check(ast.GeneratorExp(elt=elt, generators=list(generators), lineno=n.lineno), Dyn, errmsg('COMP_CHECK', self.filename, n, Dyn)), Dyn

    def visitcomprehension(self, n, env, misc, lineno):
        (iter, ity) = self.dispatch(n.iter, env, misc)
        ifs = [if_ for (if_, _) in [self.dispatch(if2, env, misc) for if2 in n.ifs]]
        (target, tty) = self.dispatch(n.target, env, misc)
        
        ety = Dyn

        if tyinstance(ity, List):
            ety = ity.type
        elif tyinstance(ity, Tuple):
            ety = tyjoin(*ity.elements)
        elif tyinstance(ity, Dict):
            ety = ity.keys

        assignments = [(target, ety)]
        new_assignments = []
        while assignments:
            k, v = assignments[0]
            del assignments[0]
            if isinstance(k, ast.Name):
                new_assignments.append((Var(k.id),v))
            elif isinstance(k, ast.Tuple) or isinstance(k, ast.List):
                if tyinstance(v, Tuple):
                    assignments += (list(zip(k.elts, v.elements)))
                elif tyinstance(v, Iterable) or tyinstance(v, List):
                    assignments += ([(e, v.type) for e in k.elts])
                elif tyinstance(v, Dict):
                    assignments += (list(zip(k.elts, v.keys)))
                else: assignments += ([(e, Dyn) for e in k.elts])
                        
        iter_target = Dyn #Iterable(tty)

        return ast.comprehension(target=target, iter=cast(env, misc.cls, iter, ity, iter_target, errmsg('ITER_ERROR', self.filename, lineno, iter_target)), 
                                 ifs=ifs), new_assignments

    # Control flow stuff
    def visitYield(self, n, env, misc):
        value, _ = self.dispatch(n.value, env, misc) if n.value else (None, Void)
        return ast.Yield(value=value, lineno=n.lineno), Dyn

    def visitYieldFrom(self, n, env, misc):
        value, _ = self.dispatch(n.value, env, misc)
        return ast.YieldFrom(value=value, lineno=n.lineno), Dyn

    def visitIfExp(self, n, env, misc):
        test, _ = self.dispatch(n.test, env, misc)
        body, bty = self.dispatch(n.body, env, misc)
        orelse, ety = self.dispatch(n.orelse, env, misc)
        return ast.IfExp(test=test, body=body, orelse=orelse, lineno=n.lineno), tyjoin([bty,ety])

    # Function stuff
    def visitCall(self, n, env, misc):
        project_needed = [False] # Python2 doesn't have nonlocal
        class BadCall(Exception):
            def __init__(self, msg):
                self.msg = msg
        def cast_args(argdata, fun, funty):
            vs, ss = zip(*argdata) if argdata else ([], [])
            vs = list(vs)
            ss = list(ss)
            if tyinstance(funty, Dyn):
                if n.keywords or n.starargs or n.kwargs:
                    targparams = DynParameters
                else: targparams = AnonymousParameters(ss)
                return vs, cast(env, misc.cls, fun, Dyn, Function(targparams, Dyn),
                                errmsg('FUNC_ERROR', self.filename, n, Function(targparams, Dyn))), Dyn
            elif tyinstance(funty, Function):
                argcasts = funty.froms.lenmatch(argdata)
                if argcasts != None:
                    return ([cast(env, misc.cls, v, s, t, errmsg('ARG_ERROR', self.filename, n, t)) for \
                                (v, s), t in argcasts],
                            fun, funty.to)
                else: 
                    raise BadCall(errmsg('BAD_ARG_COUNT', self.filename, n, len(funty.froms), len(argdata)))
            elif tyinstance(funty, Class):
                project_needed[0] = True
                if '__init__' in funty.members:
                    inst = funty.instance()
                    funty = funty.member_type('__init__')
                    if tyinstance(funty, Function):
                        funty = funty.bind()
                        funty.to = inst
                else:
                    funty = Function(DynParameters, funty.instance())
                return cast_args(argdata, fun, funty)
            elif tyinstance(funty, Object):
                if '__call__' in funty.members:
                    funty = funty.member_type('__call__')
                    return cast_args(argdata, fun, funty)
                else:
                    funty = Function(DynParameters, Dyn)
                    return cast_args(argdata, cast(env, misc.cls, fun, funty, Record({'__call__': funty}), 
                                                   errmsg('OBJCALL_ERROR', self.filename, n)),
                                     funty)
            else: raise BadCall(errmsg('BAD_CALL', self.filename, n, funty))

        (func, ty) = self.dispatch(n.func, env, misc)

        if tyinstance(ty, InferBottom):
            return n, Dyn

        argdata = [self.dispatch(x, env, misc) for x in n.args]
        try:
            (args, func, retty) = cast_args(argdata, func, ty)
        except BadCall as e:
            if flags.REJECT_WEIRD_CALLS or not (n.keywords or n.starargs or n.kwargs):
                return error(e.msg), Dyn
            else:
                warn('Function calls with keywords, starargs, and kwargs are not typechecked. Using them may induce a type error in file %s (line %d)' % (self.filename, n.lineno), 0)
                args = n.args
                retty = Dyn
        call = ast.Call(func=func, args=args, keywords=n.keywords,
                        starargs=n.starargs, kwargs=n.kwargs, lineno=n.lineno)
        if project_needed[0]:
            call = cast(env, misc.cls, call, Dyn, retty, errmsg('BAD_OBJECT_INJECTION', self.filename, n, retty, ty))
        else: call = check(call, retty, errmsg('RETURN_CHECK', self.filename, n, retty))
        return (call, retty)

    def visitLambda(self, n, env, misc):
        args, argnames, specials = self.dispatch(n.args, env, DynParameters, misc, n.lineno)
        params = [Dyn] * len(argnames)
        env = env.copy()
        env.update(dict(list(zip(argnames, params))))
        env.update(dict(specials))
        body, rty = self.dispatch(n.body, env, misc)
        if n.args.vararg:
            ffrom = DynParameters
        elif n.args.kwarg:
            ffrom = DynParameters
        elif flags.PY_VERSION == 3 and n.args.kwonlyargs:
            ffrom = DynParameters
        elif n.args.defaults:
            ffrom = DynParameters
        else: ffrom = NamedParameters(list(zip(argnames, params)))
        
        ty = Function(ffrom, rty) if flags.TYPED_LAMBDAS else Dyn

        return ast.Lambda(args=args, body=body, lineno=n.lineno), ty

    # Variable stuff
    def visitName(self, n, env, misc):
        if isinstance(n.ctx, ast.Param): # Compatibility with 2.7
            return n.id
        try:
            ty = env[Var(n.id)]
            if isinstance(n.ctx, ast.Del) and not tyinstance(ty, Dyn) and flags.REJECT_TYPED_DELETES:
                return error(errmsg('TYPED_VAR_DELETE', self.filename, n, n.id, ty)), Dyn
        except KeyError:
            ty = Dyn
        
        id = n.id if n.id not in rtypes.TYPES else n.id + '_'
        return ast.Name(id=id, ctx=n.ctx, lineno=n.lineno), ty

    def visitNameConstant(self, n, env, misc):
        if flags.TYPED_LITERALS:
            if n.value is True or n.value is False:
                return n, Bool 
            elif n.value is None:
                return n, Void 
        return n, Dyn

    def visitAttribute(self, n, env, misc):
        value, vty = self.dispatch(n.value, env, misc)

        if tyinstance(vty, InferBottom):
            return n, Dyn

        if isinstance(vty, Structural):
            vty = vty.structure()
        assert vty is not None, n.value

        if tyinstance(vty, Self):
            if not misc.cls or not misc.receiver:
                return error(errmsg('UNSCOPED_SELF', self.filename, n))
            try:
                ty = misc.cls.instance().member_type(n.attr)
            except KeyError:
                if flags.CHECK_ACCESS and not flags.CLOSED_CLASSES and not isinstance(n.ctx, ast.Store):
                    value = cast(env, misc.cls, value, misc.cls.instance(), Object(misc.cls.name, {n.attr: Dyn}), 
                                 errmsg('WIDTH_DOWNCAST', self.filename, n, n.attr))
                ty = Dyn
            if isinstance(value, ast.Name) and value.id == misc.receiver.id:
                if flags.SEMANTICS == 'MONO' and not isinstance(n.ctx, ast.Store) and not isinstance(n.ctx, ast.Del) and \
                        not tyinstance(ty, Dyn):
                    ans = ast.Call(func=ast.Name(id='retic_getattr_'+('static' if ty.static() else 'dynamic'), 
                                                 ctx=ast.Load(), lineno=n.lineno),
                                   args=[value, ast.Str(s=n.attr), ty.to_ast()],
                                   keywords=[], starargs=None, kwargs=None, lineno=n.lineno)
                    return ans, ty
                else: return ast.Attribute(value=value, attr=n.attr, lineno=n.lineno, ctx=n.ctx), ty
            if isinstance(n.ctx, ast.Store):
                return ast.Attribute(value=value, attr=n.attr, lineno=n.lineno, ctx=n.ctx), ty
            return ast.Call(func=ast.Name(id='retic_bindmethod', ctx=ast.Load()),
                            args=[ast.Attribute(value=misc.receiver, attr='__class__', ctx=ast.Load()),
                                  value, ast.Str(s=n.attr)], keywords=[], starargs=None, kwargs=None, 
                            lineno=n.lineno), \
                                  ty
        elif tyinstance(vty, Object) or tyinstance(vty, Class):
            try:
                ty = vty.member_type(n.attr)
                if isinstance(n.ctx, ast.Del):
                    return error(errmsg('TYPED_ATTR_DELETE', self.filename, n, n.attr, ty)), Dyn
            except KeyError:
                if flags.CHECK_ACCESS and not flags.CLOSED_CLASSES and not isinstance(n.ctx, ast.Store):
                    value = cast(env, misc.cls, value, vty, vty.__class__('', {n.attr: Dyn}), 
                                 errmsg('WIDTH_DOWNCAST', self.filename, n, n.attr))
                ty = Dyn
        elif tyinstance(vty, Dyn):
            if flags.CHECK_ACCESS and not isinstance(n.ctx, ast.Store) and not isinstance(n.ctx, ast.Del):
                value = cast(env, misc.cls, value, vty, Record({n.attr: Dyn}), 
                             errmsg('WIDTH_DOWNCAST', self.filename, n, n.attr)) 
            else:
                value = cast(env, misc.cls, value, vty, Record({}), 
                             errmsg('NON_OBJECT_' + ('WRITE' if isinstance(n.ctx, ast.Store) \
                                                         else 'DEL'), self.filename, n, n.attr))
            ty = Dyn
        else: 
            kind = 'WRITE' if isinstance(n.ctx, ast.Store) else ('DEL' if isinstance(n.ctx, ast.Del) else 'READ')
            return error(errmsg('NON_OBJECT_' + kind, self.filename, n, n.attr, static_val(vty))), Dyn

        if flags.SEMANTICS == 'MONO' and not isinstance(n.ctx, ast.Store) and not isinstance(n.ctx, ast.Del) and \
                not tyinstance(ty, Dyn):
            ans = ast.Call(func=ast.Name(id='retic_getattr_'+('static' if ty.static() else 'dynamic'), 
                                         ctx=ast.Load(), lineno=n.lineno),
                           args=[value, ast.Str(s=n.attr), ty.to_ast()],
                        keywords=[], starargs=None, kwargs=None, lineno=n.lineno)
            return ans, ty

        ans = ast.Attribute(value=value, attr=n.attr, ctx=n.ctx, lineno=n.lineno)
        if not isinstance(n.ctx, ast.Store) and not isinstance(n.ctx, ast.Del):
            ans = check(ans, ty, errmsg('ACCESS_CHECK', self.filename, n, n.attr, ty))
        return ans, ty

    def visitSubscript(self, n, env, misc):
        value, vty = self.dispatch(n.value, env, misc)
        if tyinstance(vty, InferBottom):
            return n, Dyn
        slice, ty = self.dispatch(n.slice, env, vty, misc, n.lineno)
        ans = ast.Subscript(value=value, slice=slice, ctx=n.ctx, lineno=n.lineno)
        if not isinstance(n.ctx, ast.Store):
            ans = check(ans, ty, errmsg('SUBSCRIPT_CHECK', self.filename, n, ty))
        return ans, ty

    def visitIndex(self, n, env, extty, misc, lineno):
        value, vty = self.dispatch(n.value, env, misc)
        err = errmsg('BAD_INDEX', self.filename, lineno, extty, Int)
        if tyinstance(extty, List):
            value = cast(env, misc.cls, value, vty, Int, err)
            ty = extty.type
        elif tyinstance(extty, Bytes):
            value = cast(env, misc.cls, value, vty, Int, err)
            ty = Int
        elif tyinstance(extty, String):
            value = cast(env, misc.cls, value, vty, Int, err)
            ty = String
        elif tyinstance(extty, Tuple):
            value = cast(env, misc.cls, value, vty, Int, err)
            ty = Dyn
        elif tyinstance(extty, Dict):
            value = cast(env, misc.cls, value, vty, extty.keys, errmsg('BAD_INDEX', self.filename, lineno, extty, extty.keys))
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
            return error(errmsg('NON_INDEXABLE', self.filename, lineno, extty)), Dyn
        # More cases...?
        return ast.Index(value=value), ty

    def visitSlice(self, n, env, extty, misc, lineno):
        err = errmsg('BAD_INDEX', self.filename, lineno, extty, Int)
        lower, lty = self.dispatch(n.lower, env, misc) if n.lower else (None, Void)
        upper, uty = self.dispatch(n.upper, env, misc) if n.upper else (None, Void)
        step, sty = self.dispatch(n.step, env, misc) if n.step else (None, Void)
        if any(tyinstance(extty, kind) for kind in [List, Tuple, String, Bytes]):
            lower = cast(env, misc.cls, lower, lty, Int, err) if lty != Void else lower
            upper = cast(env, misc.cls, upper, uty, Int, err) if uty != Void else upper
            step = cast(env, misc.cls, step, sty, Int, err) if sty != Void else step
            ty = extty
        elif tyinstance(extty, Object) or tyinstance(extty, Class):
            # Expand
            ty = Dyn
        elif tyinstance(extty, Dyn):
            ty = Dyn
        else: 
            return error(errmsg('NON_SLICEABLE', self.filename, n, extty)), Dyn
        return ast.Slice(lower=lower, upper=upper, step=step), ty

    def visitExtSlice(self, n, env, extty, misc, lineno):
        dims = [dim for (dim, _) in [self.dispatch(dim2, env, extty, misc, lineno) for dim2 in n.dims]]
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
        return ast.Starred(value=value, ctx=n.ctx, lineno=n.lineno), Dyn

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
        return (n, ty if flags.TYPED_LITERALS else Dyn)

    def visitStr(self, n, env, misc):
        return (n, String if flags.TYPED_LITERALS else Dyn)

    def visitBytes(self, n, env, misc):
        return (n, Bytes if flags.TYPED_LITERALS else Dyn)
