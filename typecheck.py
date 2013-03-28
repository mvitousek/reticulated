from __future__ import print_function
import ast
from vis import Visitor
from typefinder import Typefinder
from typing import *
from relations import *
from exc import StaticTypeError
import typing, ast, utils, flags


WILL_FALL_OFF = 2
MAY_FALL_OFF = 1
WILL_RETURN = 0


def meet_mfo(m1, m2):
    return max(m1, m2)

def warn(msg):
    if flags.VERBOSE:
        print('WARNING:', msg)


##Cast insertion functions##
#Normal casts
def cast(val, src, trg, msg, cast_function='retic_cast'):
    src = normalize(src)
    trg = normalize(trg)

    lineno = str(val.lineno) if hasattr(val, 'lineno') else 'number missing'
    if not subcompat(src, trg):
        return error("%s: cannot cast from %s to %s (line %s)" % (msg, src, trg, lineno))
    elif src == trg:
        return val
    elif not flags.OPTIMIZED_INSERTION:
        warn('Inserting cast at line %s: %s => %s' % (lineno, src, trg))
        return ast.Call(func=ast.Name(id=cast_function, ctx=ast.Load()),
                        args=[val, src.to_ast(), trg.to_ast(), ast.Str(s=msg)],
                        keywords=[], starargs=None, kwargs=None)
    else:
        # Specialized version that omits unnecessary casts depending what mode we're in,
        # e.g. cast-as-assert would omit naive upcasts
        pass

# Casting with unknown source type, as in cast-as-assertion 
# function return values at call site
def check(val, trg, msg, check_function='retic_check', lineno=None):
    trg = normalize(trg)
    if lineno == None:
        lineno = str(val.lineno) if hasattr(val, 'lineno') else 'number missing'

    if not flags.OPTIMIZED_INSERTION:
        warn('Inserting check at line %s: %s' % (lineno, trg))
        return ast.Call(func=ast.Name(id=check_function, ctx=ast.Load()),
                        args=[val, trg.to_ast(), ast.Str(s=msg)],
                        keywords=[], starargs=None, kwargs=None)
    else:
        if flags.SEMANTICS == 'CAC':
            warn('Inserting check at line %s: %s' % (lineno, trg))
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
        if ckhval == val:
            return []
        else: return [ast.Expr(value=chkval, lineno=lineno)]

# Insert a call to an error function if we've turned off static errors
def error(msg, error_function='retic_error'):
    if flags.STATIC_ERRORS:
        raise StaticTypeError(msg)
    else:
        warn('Static error found')
        return ast.Call(func=ast.Name(id=error_function, ctx=ast.Load()),
                        args=[ast.Str(s=msg+' (statically detected)')], keywords=[], starargs=None,
                        kwargs=None)

# Error, but within an expression statement
def error_stmt(msg, lineno, mfo=MAY_FALL_OFF, error_function='retic_error'):
    if flags.STATIC_ERRORS:
        raise StaticTypeError(msg)
    else:
        return ast.Expr(value=error(msg, error_function), lineno=lineno), mfo

class Typechecker(Visitor):
    typefinder = Typefinder()
    
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

    def typecheck(self, n):
        n = ast.fix_missing_locations(n)
        n = self.preorder(n, {})
        n = ast.fix_missing_locations(n)
        return n

    def dispatch_scope(self, n, env, ret, initial_locals={}):
        env = env.copy()
        env.update(self.typefinder.dispatch_scope(n, env, initial_locals))
        body = []
        fo = MAY_FALL_OFF
        wfo = False
        for s in n:
            (stmt, fo) = self.dispatch(s, env, ret)
            body.append(stmt)
            if not wfo and fo == WILL_FALL_OFF:
                wfo = True
        return (body, fo if not wfo else MAY_FALL_OFF)

    def dispatch_statements(self, n, env, ret):
        body = []
        fo = MAY_FALL_OFF
        wfo = False
        for s in n:
            (stmt, fo) = self.dispatch(s, env, ret)
            body.append(stmt)
            if not wfo and fo == WILL_FALL_OFF:
                wfo = True
        return (body, fo if not wfo else MAY_FALL_OFF)
        
    def visitModule(self, n, env):
        (body, fo) = self.dispatch_scope(n.body, env, Void)
        return ast.Module(body=body)

## STATEMENTS ##
    # Import stuff
    def visitImport(self, n, env, ret):
        return (n, MAY_FALL_OFF)

    def visitImportFrom(self, n, env, ret):
        return (n, MAY_FALL_OFF)

    # Function stuff
    def visitFunctionDef(self, n, env, ret): #TODO: check defaults, handle varargs and kwargs
        args, argnames = self.dispatch(n.args, env)
        decorator_list = [self.dispatch(dec, env)[0] for dec in n.decorator_list if not is_annotation(dec)]
        nty = env[n.name]
        
        env = env.copy()
        argtys = list(zip(argnames, nty.froms))
        initial_locals = dict(argtys + [(n.name, nty)])
        (body, fo) = self.dispatch_scope(n.body, env, nty.to, initial_locals)
        
        argchecks = sum((check_stmtlist(ast.Name(id=arg, ctx=ast.Load()), ty, 'Argument of incorrect type', lineno=n.lineno) \
                             for (arg, ty) in argtys), [])

        if nty.to != Dyn and nty.to != Void and fo == MAY_FALL_OFF:
            return error_stmt('Return value of incorrect type', n.lineno)

        if PY_VERSION == 3:
            return (ast.FunctionDef(name=n.name, args=args,
                                    body=argchecks+body, decorator_list=decorator_list,
                                    returns=n.returns, lineno=n.lineno), MAY_FALL_OFF)
        elif PY_VERSION == 2:
            return (ast.FunctionDef(name=n.name, args=args,
                                    body=argchecks+body, decorator_list=decorator_list,
                                    lineno=n.lineno), MAY_FALL_OFF)
        
            

    def visitarguments(self, n, env):
        return n, [self.dispatch(arg, env) for arg in n.args]
    
    def visitarg(self, n, env):
        return n.arg

    def visitReturn(self, n, env, ret):
        if n.value:
            (value, ty) = self.dispatch(n.value, env)
            mfo = MAY_FALL_OFF if tyinstance(ty, Void) else WILL_RETURN
            value = cast(value, ty, ret, "Return value of incorrect type")
        else:
            mfo = MAY_FALL_OFF
            value = None
            if not subcompat(Void, ret):
                return error_stmt('Return value expected', n.lineno, mfo)
        return (ast.Return(value=value, lineno=n.lineno), mfo)

    # Assignment stuff
    def visitAssign(self, n, env, ret):
        (val, vty) = self.dispatch(n.value, env)
        ttys = []
        targets =[]
        for target in n.targets:
            (target, tty) = self.dispatch(target, env)
            ttys.append(tty)
            targets.append(target)
        try:
            meet = tymeet(ttys)
        except Bot:
            return error_stmt('Assignee of incorrect type', n.lineno)

        val = cast(val, vty, meet, "Assignee of incorrect type")
        return (ast.Assign(targets=targets, value=val, lineno=n.lineno), MAY_FALL_OFF)

    def visitAugAssign(self, n, env, ret):
        (target, tty) = self.dispatch(n.target, env)
        (value, _) = self.dispatch(n.value, env)
        optarget = utils.copy_assignee(target, ast.Load())

        assignment = ast.Assign(targets=[target], 
                                value=ast.BinOp(left=optarget,
                                                op=n.op,
                                                right=value),
                                lineno=n.lineno)
        
        return self.dispatch(assignment, env, ret)

    def visitDelete(self, n, env, ret):
        targets = []
        for t in n.targets:
            (value, ty) = self.dispatch(t, env)
            targets.append(value)
        return (ast.Delete(targets=targets, lineno=n.lineno), MAY_FALL_OFF)

    # Control flow stuff
    def visitIf(self, n, env, ret):
        (test, tty) = self.dispatch(n.test, env)
        (body, bfo) = self.dispatch_statements(n.body, env, ret)
        (orelse, efo) = self.dispatch_statements(n.orelse, env, ret) if n.orelse else ([], MAY_FALL_OFF)
        mfo = meet_mfo(bfo, efo)
        return (ast.If(test=test, body=body, orelse=orelse, lineno=n.lineno), mfo)

    def visitFor(self, n, env, ret):
        (target, tty) = self.dispatch(n.target, env)
        (iter, ity) = self.dispatch(n.iter, env)
        (body, bfo) = self.dispatch_statements(n.body, env, ret)
        (orelse, efo) = self.dispatch_statements(n.orelse, env, ret) if n.orelse else ([], MAY_FALL_OFF)
        
        targcheck = check_stmtlist(utils.copy_assignee(target, ast.Load()),
                                   tty, 'Iterator of incorrect type', lineno=n.lineno)
        mfo = meet_mfo(bfo, efo)
        return (ast.For(target=target, iter=cast(iter, ity, Iterable(tty), 'iterator list of incorrect type'),
                        body=targcheck+body, orelse=orelse, lineno=n.lineno), mfo)
        
    def visitWhile(self, n, env, ret):
        (test, tty) = self.dispatch(n.test, env)
        (body, bfo) = self.dispatch_statements(n.body, env, ret)
        (orelse, efo) = self.dispatch_statements(n.orelse, env, ret) if n.orelse else ([], MAY_FALL_OFF)
        mfo = meet_mfo(bfo, efo)
        return (ast.While(test=test, body=body, orelse=orelse, lineno=n.lineno), mfo)

    def visitWith(self, n, env, ret): #2.7, 3.2 -- UNDEFINED FOR 3.3 right now
        (context_expr, _) = self.dispatch(n.context_expr, env)
        (optional_vars, _) = self.dispatch(n.optional_vars, env) if n.optional_vars else (None, Dyn)
        (body, mfo) = self.dispatch_statements(n.body, env, ret)
        return (ast.With(context_expr=context_expr, optional_vars=optional_vars, body=body, lineno=n.lineno), mfo)
    
    # Class stuff
    def visitClassDef(self, n, env, ret): #Keywords, kwargs, etc
        bases = [self.dispatch(base, env)[0] for base in n.bases]
        nty = env[n.name]
        env = env.copy()
        
        initial_locals = {n.name: nty}
        (body, _) = self.dispatch_scope(n.body, env, Void, initial_locals)

        if PY_VERSION == 3:
            return (ast.ClassDef(name=n.name, bases=bases, keywords=n.keywords,
                                 starargs=n.starargs, kwargs=n.kwargs, body=body,
                                 decorator_list=n.decorator_list, lineno=n.lineno), 
                    MAY_FALL_OFF)     
        elif PY_VERSION == 2:
            return (ast.ClassDef(name=n.name, bases=bases, body=body,
                                 decorator_list=n.decorator_list, lineno=n.lineno), 
                    MAY_FALL_OFF)     

    # Exception stuff
    # Python 2.7, 3.2
    def visitTryExcept(self, n, env, ret):
        (body, mfo) = self.dispatch_statements(n.body, env, ret)
        handlers = []
        for handler in n.handlers:
            (handler, hfo) = self.dispatch(handler, env, ret)
            mfo = meet_mfo(mfo, hfo)
            handlers.append(handler)
        (orelse, efo) = self.dispatch(n.orelse, env, ret) if n.orelse else ([], mfo)
        mfo = meet_mfo(mfo, efo)
        return (ast.TryExcept(body=body, handlers=handlers, orelse=orelse, lineno=n.lineno), mfo)

    # Python 2.7, 3.2
    def visitTryFinally(self, n, env, ret):
        (body, bfo) = self.dispatch_statements(n.body, env, ret)
        (finalbody, ffo) = self.dispatch_statements(n.finalbody, env, ret)
        if ffo == WILL_RETURN:
            return (TryFinally(body=body, finalbody=finalbody, lineno=n.lineno), ffo)
        else:
            return (TryFinally(body=body, finalbody=finalbody, lineno=n.lineno), bfo)
    
    # Python 3.3
    def visitTry(self, n, env, ret):
        (body, mfo) = self.dispatch_statements(n.body, env, ret)
        handlers = []
        for handler in n.handlers:
            (handler, hfo) = self.dispatch(handler, env, ret)
            mfo = meet_mfo(mfo, hfo)
            handlers.append(handler)
        (orelse, efo) = self.dispatch(n.orelse, env, ret) if n.orelse else ([], mfo)
        mfo = meet_mfo(mfo, efo)
        (finalbody, ffo) = self.dispatch_statements(n.finalbody, env, ret)
        if ffo == WILL_RETURN:
            return (Try(body=body, handlers=handlers, orelse=orelse, finalbody=finalbody, lineno=n.lineno), ffo)
        else:
            return (Try(body=body, handlers=handlers, orelse=orelse, finalbody=finalbody, lineno=n.lineno), mfo)

    def visitExceptHandler(self, n, env, ret):
        (type, tyty) = self.dispatch(n.type, env) if n.type else (None, Dyn)
        (body, mfo) = self.dispatch_statements(n.body, env, ret)
        if PY_VERSION == 2 and n.name and type:
            name, nty = self.dispatch(n.name, env)
            type = cast(type, tyty, nty, "Incorrect exception type")
        else: 
            name = n.name
        return (ast.ExceptHandler(type=type, name=name, body=body, lineno=n.lineno), mfo)

    def visitRaise(self, n, env, ret):
        if PY_VERSION == 3:
            (exc, _) = self.dispatch(n.exc, env) if n.exc else (None, Dyn)
            (cause, _) = self.dispatch(n.cause, env) if n.cause else (None, Dyn)
            return (ast.Raise(exc=exc, cause=cause, lineno=n.lineno), WILL_RETURN)
        elif PY_VERSION == 2:
            (type, _) = self.dispatch(n.type, env) if n.type else (None, Dyn)
            (inst, _) = self.dispatch(n.inst, env) if n.inst else (None, Dyn)
            (tback, _) = self.dispatch(n.tback, env) if n.tback else (None, Dyn)
            return ast.Raise(type=type, inst=inst, tback=tback, lineno=n.lineno), WILL_RETURN

    def visitAssert(self, n, env, ret):
        (test, _) = self.dispatch(n.test, env)
        (msg, _) = self.dispatch(n.msg, env) if n.msg else (None, Dyn)
        return (ast.Assert(test=test, msg=msg, lineno=n.lineno), MAY_FALL_OFF)

    # Declaration stuff
    def visitGlobal(self, n, env, ret):
        return (n, MAY_FALL_OFF)

    def visitNonlocal(self, n, env, ret):
        return (n, MAY_FALL_OFF)

    # Miscellaneous
    def visitExpr(self, n, env, ret):
        (value, ty) = self.dispatch(n.value, env)
        return (ast.Expr(value=value, lineno=n.lineno), MAY_FALL_OFF)

    def visitPass(self, n, env, ret):
        return (n, MAY_FALL_OFF)

    def visitBreak(self, n, env, ret):
        return (n, WILL_FALL_OFF)

    def visitContinue(self, n, env, ret):
        return (n, MAY_FALL_OFF)

    def visitPrint(self, n, env, ret):
        dest, _ = self.dispatch(n.dest, env) if n.dest else (None, Void)
        values = [self.dispatch(val, env)[0] for val in n.values]
        return ast.Print(dest=dest, values=values, nl=n.nl), MAY_FALL_OFF

    def visitExec(self, n, env, ret):
        body, _ = self.dispatch(n.body, env)
        globals, _ = self.dispatch(n.globals, env) if n.globals else (None, Void)
        locals, _ = self.dispatch(n.locals, env) if n.locals else (None, Void)
        return ast.Exec(body=body, globals=globals, locals=locals), MAY_FALL_OFF

### EXPRESSIONS ###
    # Op stuff
    def visitBoolOp(self, n, env):
        values = []
        tys = []
        for value in n.values:
            (value, ty) = self.dispatch(value, env)
            values.append(value)
            tys.append(ty)
        ty = tyjoin(tys)
        return (ast.BoolOp(op=n.op, values=values), ty)

    def visitBinOp(self, n, env):
        (left, lty) = self.dispatch(n.left, env)
        (right, rty) = self.dispatch(n.right, env)
        node = ast.BinOp(left=left, op=n.op, right=right)
        try:
            ty = binop_type(lty, n.op, rty)
        except Bot:
            return error('Incompatible types for binary operation'), Dyn
        return (node, ty)

    def visitUnaryOp(self, n, env):
        (operand, ty) = self.dispatch(n.operand, env)
        node = ast.UnaryOp(op=n.op, operand=operand)
        if isinstance(n.op, ast.Invert):
            ty = primjoin([ty], Int, Int)
        elif any([isinstance(n.op, op) for op in [ast.UAdd, ast.USub]]):
            ty = primjoin([ty])
        elif isinstance(n.op, ast.Not):
            ty = Bool
        return (node, ty)

    def visitCompare(self, n, env):
        (left, _) = self.dispatch(n.left, env)
        comparators = [comp for (comp, _) in [self.dispatch(ocomp, env) for ocomp in n.comparators]]
        return (ast.Compare(left=left, ops=n.ops, comparators=comparators), Bool)

    # Collections stuff    
    def visitList(self, n, env):
        eltdata = [self.dispatch(x, env) for x in n.elts]
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

    def visitTuple(self, n, env):
        eltdata = [self.dispatch(x, env) for x in n.elts]
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

    def visitDict(self, n, env):
        keydata = [self.dispatch(key, env) for key in n.keys]
        valdata = [self.dispatch(val, env) for val in n.values]
        keys, ktys = list(zip(*keydata)) if keydata else ([], [])
        values, vtys = list(zip(*valdata)) if valdata else ([], [])
        return (ast.Dict(keys=list(keys), values=list(values)), Dict(tyjoin(list(ktys)), tyjoin(list(vtys))))

    def visitSet(self, n, env):
        eltdata = [self.dispatch(x, env) for x in n.elts]
        elttys = [ty for (elt, ty) in eltdata]
        ty = tyjoin(elttys)
        elts = [elt for (elt, ty) in eltdata]
        return (ast.Set(elts=elts), Set(ty))

    def visitListComp(self, n, env):
        generators = [self.dispatch(generator, env) for generator in n.generators]
        elt, ety = self.dispatch(n.elt, env)
        return check(ast.ListComp(elt=elt, generators=generators), List(ety), 'List comprehension of incorrect type', lineno=n.lineno), List(ety)

    def visitSetComp(self, n, env):
        generators = [self.dispatch(generator, env) for generator in n.generators]
        elt, ety = self.dispatch(n.elt, env)
        return check(ast.SetComp(elt=elt, generators=generators), Set(ety), 'Set comprehension of incorrect type', lineno=n.lineno), Set(ety)

    def visitDictComp(self, n, env):
        generators = [self.dispatch(generator, env) for generator in n.generators]
        key, kty = self.dispatch(n.key, env)
        value, vty = self.dispatch(n.value, env)
        return check(ast.DictComp(key=key, value=value, generators=generators), Dict(kty, vty), 'Dict comprehension of incorrect type', lineno=n.lineno), Dict(kty, vty)

    def visitGeneratorExp(self, n, env):
        generators = [self.dispatch(generator, env) for generator in n.generators]
        elt, ety = self.dispatch(n.elt, env)
        return check(ast.GeneratorExp(elt=elt, generators=generators), Iterable(ety), 'Comprehension of incorrect type', lineno=n.lineno), Iterable(ety)

    def visitcomprehension(self, n, env):
        (iter, ity) = self.dispatch(n.iter, env)
        ifs = [if_ for (if_, _) in [self.dispatch(if2, env) for if2 in n.ifs]]
        (target, tty) = self.dispatch(n.target, env)
        return ast.comprehension(target=target, iter=cast(iter, ity, Iterable(tty), 'Iterator list of incorrect type'), ifs=ifs)

    # Control flow stuff
    def visitYield(self, n, env):
        value, _ = self.dispatch(n.value, env) if n.value else (None, Void)
        return ast.Yield(value=value), Dyn

    def visitYieldFrom(self, n, env):
        value, _ = self.dispatch(n.value, env)
        return ast.YieldFrom(value=value), Dyn

    def visitIfExp(self, n, env):
        test, _ = self.dispatch(n.test, env)
        body, bty = self.dispatch(n.body, env)
        orelse, ety = self.dispatch(n.orelse, env)
        return ast.IfExp(test=test, body=body, orelse=orelse), tyjoin([bty,ety])

    # Function stuff
    def visitCall(self, n, env):
        def cast_args(argdata, fun, funty):
            if any([tyinstance(funty, x) for x in UNCALLABLES]):
                return error(''), Dyn
            elif tyinstance(funty, Dyn):
                return ([v for (v, s) in argdata],
                        cast(fun, Dyn, Function([s for (v, s) in argdata], Dyn), 
                             "Function of incorrect type"),
                        Dyn)
            elif tyinstance(funty, Function):
                if len(argdata) <= len(funty.froms):
                    args = [cast(v, s, t, "Argument of incorrect type") for ((v, s), t) in 
                            zip(argdata, funty.froms)]
                    return (args, fun, funty.to)
                else: return error(''), Dyn
            elif tyinstance(funty, Object):
                if '__call__' in ty.members:
                    funty = funty.members['__call__']
                    return cast_args(args, atys, funty)
                else: return ([cast(v, s, Dyn, "Argument of incorrect type") for (v, s) in
                               argdata], fun, Dyn)
            else: return ([cast(v, s, Dyn, "Argument of incorrect type") for (v, s) in
                           argdata], fun, Dyn)

        (func, ty) = self.dispatch(n.func, env)
        argdata = [self.dispatch(x, env) for x in n.args]
        (args, func, ret) = cast_args(argdata, func, ty)
        call = ast.Call(func=func, args=args, keywords=n.keywords,
                        starargs=n.starargs, kwargs=n.kwargs)
        call = check(call, ret, "Return value of incorrect type", lineno=n.lineno)
        return (call, ret)

    def visitLambda(self, n, env):
        args, argnames = self.dispatch(n.args, env)
        params = [Dyn] * len(argnames)
        env = env.copy()
        env.update(dict(list(zip(argnames, params))))
        body, rty = self.dispatch(n.body, env)
        return ast.Lambda(args=args, body=body), Function(params, rty)

    # Variable stuff
    def visitName(self, n, env):
        if isinstance(n.ctx, ast.Param): # Compatibility with 2.7
            return n.id
        try:
            ty = env[n.id]
            if isinstance(n.ctx, ast.Del) and not tyinstance(ty, Dyn):
                return error('Attempting to delete statically typed id'), ty
        except KeyError:
            ty = Dyn
        return (n, ty)

    def visitAttribute(self, n, env):
        value, vty = self.dispatch(n.value, env)
        if tyinstance(vty, Object) or hasattr(vty, 'structure'):
            if not isinstance(vty, Object):
                vty = vty.structure()
            try:
                ty = vty.members[n.attr]
                if isinstance(n.ctx, ast.Del):
                    return error('Attempting to delete statically typed attribute'), ty
            except KeyError:
                if not isinstance(n.ctx, ast.Store):
                    value = cast(value, vty, Object({n.attr: Dyn}), 'Attempting to access nonexistant attribute')
                ty = Dyn
        elif tyinstance(vty, Dyn):
            if not isinstance(n.ctx, ast.Store):
                value = cast(value, vty, Object({n.attr: Dyn}), 'Attempting to access nonexistant attribute') 
            else:
                value = cast(value, vty, Object({}), 'Attempting to access from non-object') 
            ty = Dyn
        else: error('Attempting to access from non-object')
        ans = ast.Attribute(value=value, attr=n.attr, ctx=n.ctx)
        if not isinstance(n.ctx, ast.Store) and not isinstance(n.ctx, ast.Del):
            ans = check(ans, ty, 'Value of incorrect type in object')
        return ans, ty

    def visitSubscript(self, n, env):
        value, vty = self.dispatch(n.value, env)
        slice, ty = self.dispatch(n.slice, env, vty)
        ans = ast.Subscript(value=value, slice=slice, ctx=n.ctx)
        if not isinstance(n.ctx, ast.Store):
            ans = check(ans, ty, 'Value of incorrect type in subscriptable', lineno=n.lineno)
        return ans, ty

    def visitIndex(self, n, env, extty):
        value, vty = self.dispatch(n.value, env)
        if tyinstance(extty, List):
            value = cast(value, vty, Int, 'Indexing with non-integer type')
            ty = extty.type
        elif tyinstance(extty, String) or tyinstance(extty, Tuple):
            value = cast(value, vty, Int, 'Indexing with non-integer type')
            ty = String
        elif tyinstance(extty, Dict):
            value = cast(value, vty, extty.keys, 'Indexing dict with non-key value')
            ty = extty.values
        elif tyinstance(extty, Object):
            # Expand
            ty = Dyn
        elif tyinstance(extty, Dyn):
            ty = Dyn
        else: 
            return error('Attmpting to index non-indexable value'), Dyn
        # More cases...?
        return ast.Index(value=value), ty

    def visitSlice(self, n, env, extty):
        lower, lty = self.dispatch(n.lower, env) if n.lower else (None, Void)
        upper, uty = self.dispatch(n.upper, env) if n.upper else (None, Void)
        step, sty = self.dispatch(n.step, env) if n.step else (None, Void)
        if tyinstance(extty, List):
            lower = cast(lower, vty, Int, 'Indexing with non-integer type') if lty != Void else lower
            upper = cast(upper, vty, Int, 'Indexing with non-integer type') if uty != Void else upper
            step = cast(step, vty, Int, 'Indexing with non-integer type') if sty != Void else step
            ty = extty
        elif tyinstance(extty, Object):
            # Expand
            ty = Dyn
        elif tyinstance(extty, Dyn):
            ty = Dyn
        else: 
            return error('Attmpting to slice non-sliceable value'), Dyn
        return ast.Slice(lower=lower, upper=upper, step=step), ty

    def visitExtSlice(self, n, env, extty):
        dims = [dim for (dim, _) in [self.dispatch(dim2, n, env, extty) for dim2 in n.dims]]
        return ast.ExtSlice(dims=dims), Dyn

    def visitEllipsis(self, n, env, *args): 
        #Yes, this looks stupid, but Ellipses are different kinds of things in Python 2 and 3 and if we ever
        #support them meaningfully this distinction will be crucial
        if PY_VERSION == 2: 
            extty = args[0]
            return (n, Dyn)
        elif PY_VERSION == 3:
            return (n, Dyn)

    def visitStarred(self, n, env):
        value, _ = self.dispatch(n.value, env)
        return ast.Starred(value=value, ctx=n.ctx), Dyn

    # Literal stuff
    def visitNum(self, n, env):
        ty = Dyn
        v = n.n
        if type(v) == int or (PY_VERSION == 2 and type(v) == long):
            ty = Int
        elif type(v) == float:
            ty = Float
        elif type(v) == complex:
            ty = Complex
        return (n, ty)

    def visitStr(self, n, env):
        return (n, String)

    def visitBytes(self, n, env):
        return (n, Dyn)
