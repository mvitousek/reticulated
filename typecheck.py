import ast
from vis import Visitor
from typefinder import Typefinder
from typing import *
from relations import *
from exceptions import StaticTypeError
import typing, ast

PRINT_WARNINGS = True
DEBUG_VISITOR = False
OPTIMIZED_INSERTION = False

MAY_FALL_OFF = 1
WILL_RETURN = 0

def meet_mfo(m1, m2):
    if m1 == MAY_FALL_OFF or m2 == MAY_FALL_OFF:
        return MAY_FALL_OFF
    else:
        return WILL_RETURN

def warn(msg):
    if PRINT_WARNINGS:
        print('WARNING:', msg)

def cast(val, src, trg, msg, cast_function='retic_cas_cast'):
    src = normalize(src)
    trg = normalize(trg)

    lineno = str(val.lineno) if hasattr(val, 'lineno') else 'number missing'
    if not tycompat(src, trg):
        raise StaticTypeError("%s: cannot cast from %s to %s (line %s)" % (msg, src, trg, lineno))
    elif src == trg:
        return val
    elif not OPTIMIZED_INSERTION:
        warn('Inserting cast at line %s' % lineno)
        return ast.Call(func=ast.Name(id=cast_function, ctx=ast.Load()),
                        args=[val, src.to_ast(), trg.to_ast(), ast.Str(s=msg)],
                        keywords=[], starargs=None, kwargs=None)
    else:
        # Specialized version that omits unnecessary casts depending what mode we're in,
        # e.g. cast-as-assert would omit naive upcasts
        pass

# Casting with unknown source type, as in cast-as-assertion 
# function return values at call site
def agnostic_cast(val, trg, msg, cast_function='retic_cas_check'):
    trg = normalize(trg)
    if not OPTIMIZED_INSERTION:
        return ast.Call(func=ast.Name(id=cast_function, ctx=ast.Load()),
                        args=[val, trg.to_ast(), ast.Str(s=msg)],
                        keywords=[], starargs=None, kwargs=None)
    else:
        # Specialized version that omits unnecessary casts depending what mode we're in,
        # e.g. this should be a no-op for everything but cast-as-assertion
        pass

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

    if DEBUG_VISITOR:
        dispatch = dispatch_debug

    def typecheck(self, n):
        n = self.preorder(n, {})
        n = ast.fix_missing_locations(n)
        return n

    def dispatch_scope(self, n, env, ret, initial_locals={}):
        env = env.copy()
        env.update(self.typefinder.dispatch_scope(n, env, initial_locals))
        body = []
        fo = MAY_FALL_OFF
        print ('scope in',env)
        for s in n:
            (stmt, fo) = self.dispatch(s, env, ret)
            body.append(stmt)
        return (body, fo)

    def dispatch_statements(self, n, env, ret):
        body = []
        fo = MAY_FALL_OFF
        for s in n:
            (stmt, fo) = self.dispatch(s, env, ret)
            body.append(stmt)
        return (body, fo)
        
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
        argnames = []
        for arg in n.args.args:
            argnames.append(arg.arg)
        nty = env[n.name]
        
        env = env.copy()
        argtys = zip(argnames, nty.froms)
        initial_locals = dict(list(argtys) + [(n.name, nty)])
        (body, fo) = self.dispatch_scope(n.body, env, nty.to, initial_locals)
        
        argchecks = [ast.Expr(value=agnostic_cast(ast.Name(id=arg, ctx=ast.Load()), ty, 'Argument of incorrect type'),
                              lineno=n.lineno) for
                     (arg, ty) in argtys]

        if nty.to != Dyn and nty.to != Void and fo == MAY_FALL_OFF:
            raise StaticTypeError('Return value of incorrect type')

        return (ast.FunctionDef(name=n.name, args=n.args,
                                 body=argchecks+body, decorator_list=n.decorator_list,
                                 returns=n.returns, lineno=n.lineno), MAY_FALL_OFF)

    def visitReturn(self, n, env, ret):
        if n.value:
            (value, ty) = self.dispatch(n.value, env)
            mfo = MAY_FALL_OFF if tyinstance(ty, Void) else WILL_RETURN
            value = cast(value, ty, ret, "Return value of incorrect type")
        else:
            mfo = MAY_FALL_OFF
            value = None
            if not tycompat(Void, ret):
                raise StaticTypeError('Return value expected')
        return (ast.Return(value=value, lineno=n.lineno), mfo)

    # Assignment stuff
    def visitAssign(self, n, env, ret): #handle multiple targets
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
            raise StaticTypeError('Assignee of incorrect type')
        val = cast(val, vty, meet, "Assignee of incorrect type")
        return (ast.Assign(targets=targets, value=val, lineno=n.lineno), MAY_FALL_OFF)

    def visitAugAssign(self, n, env, ret):
        (target, tty) = self.dispatch(n.target, env)
        (value, vty) = self.dispatch(n.value, env)
        if tyinstance(tty, Int):
            if isinstance(n.op, ast.Div):
                raise StaticTypeError('Incorrect operand type')
            else: vtarg = Int
        elif tyinstance(tty, Float):
            if any([isinstance(n.op, cls) for cls in
                    [ast.Add, ast.Sub, ast.Mult, ast.Pow, 
                     ast.Mod, ast.FloorDiv, ast.Div]]):     
                vtarg = Float
            else: raise StaticTypeError('Incorrect operand type')
        elif tyinstance(tty, Complex):
            if any([isinstance(n.op, cls) for cls in
                    [ast.Add, ast.Sub, ast.Mult, ast.Pow, ast.Div]]):     
                vtarg = Complex
            else: raise StaticTypeError('Incorrect operand type')
        elif tyinstance(tty, Bool):
            if any([isinstance(n.op, cls) for cls in
                    [ast.BitOr, ast.BitAnd, ast.BitXor]]):     
                vtarg = Bool
            else: raise StaticTypeError('Incorrect operand type')
        elif tyinstance(tty, String):
            if isinstance(n.op, ast.Add):
                vtarg = String
            elif isinstance(n.op, ast.Mult):
                vtarg = Int
            else: raise StaticTypeError('Incorrect operand type')
        elif tyinstance(tty, Dyn):
            vtarg = Dyn
        else:
            vtarg = Dyn # More complex logic here probably, maybe turn this into an Assign
                           
        return (ast.AugAssign(target=target, op=n.op, value=cast(value, vty, vtarg, "Incorrect operand type"), 
                           lineno=n.lineno), MAY_FALL_OFF)

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
        (orelse, efo) = self.dispatch_statements(n.orelse, env, ret) if n.orelse else (None, MAY_FALL_OFF)
        mfo = meet_mfo(bfo, efo)
        return (ast.If(test=test, body=body, orelse=orelse, lineno=n.lineno), mfo)

    def visitFor(self, n, env, ret):
        (target, tty) = self.dispatch(n.target, env)
        (iter, ity) = self.dispatch(n.iter, env)
        (body, bfo) = self.dispatch_statements(n.body, env, ret)
        (orelse, efo) = self.dispatch_statements(n.orelse, env, ret) if n.orelse else (None, MAY_FALL_OFF)
        mfo = meet_mfo(bfo, efo)
        return (ast.For(target=target, iter=iter, body=body, orelse=orelse, lineno=n.lineno), mfo)
        
    def visitWhile(self, n, env, ret):
        (test, tty) = self.dispatch(n.test, env)
        (body, bfo) = self.dispatch_statements(n.body, env, ret)
        (orelse, efo) = self.dispatch_statements(n.orelse, env, ret) if n.orelse else (None, MAY_FALL_OFF)
        mfo = meet_mfo(bfo, efo)
        return (ast.For(target=target, iter=iter, body=body, orelse=orelse, lineno=n.lineno), mfo)

    def visitWith(self, n, env, ret): #Seems like this is one of the few cases where we can impose structural types
        (context_expr, _) = self.dispatch(n.context_expr, env)
        (optional_vars, _) = self.dispatch(n.optional_vars, env) if n.optional_vars else (None, Dyn)
        (body, mfo) = self.dispatch_statements(n.body, env, ret)
        return (ast.With(context_expr=context_expr, optional_vars=optional_vars, body=body, lineno=n.lineno), mfo)
    
    # Class stuff
    def visitClassDef(self, n, env, ret):
        return (n, MAY_FALL_OFF)

    # Exception stuff
    # Python 3.2
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

    # Python 3.2
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
        (type, _) = self.dispatch(n.type, env) if n.type else (None, Dyn)
        (body, mfo) = self.dispatch_statements(n.body, env, ret)
        return (ast.ExceptHandler(type=type, name=n.name, lineno=n.lineno), mfo)

    def visitRaise(self, n, env, ret):
        (exc, _) = self.dispatch(n.exc, env) if n.exc else (None, Dyn) # Can require to be a subtype of Exception
        (cause, _) = self.dispatch(n.cause, env) if n.cause else (None, Dyn) # Same
        return (ast.Raise(exc=exc, cause=cause, lineno=n.lineno), WILL_RETURN)

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
        return (n, MAY_FALL_OFF)

    def visitContinue(self, n, env, ret):
        return (n, MAY_FALL_OFF)

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
        stringy = tyinstance(lty, String) or tyinstance(rty, String)
        if isinstance(n.op, ast.Div):
            ty = prim_join([lty, rty], Float, Complex)
        elif isinstance(n.op, ast.Add):
            if stringy:
                if tyinstance(lty, String) and tyinstance(rty, String):
                    ty = String
                else:
                    ty = Dyn
            else: ty = prim_join([lty, rty])
        elif any([isinstance(n.op, op) for op in [ast.Sub, ast.Pow]]):
            ty = prim_join([lty, rty])
        elif isinstance(n.op, ast.Mult):
            if stringy:
                if any([tyinstance(ty, String) for ty in [lty, rty]]) and \
                        any([tyinstance(ty, Int) for ty in [lty, rty]]):
                    ty = String
                else: ty = Dyn
            else: ty = prim_join([lty, rty])
        elif any([isinstance(n.op, op) for op in [ast.FloorDiv, ast.Mod]]):
            ty = ty_join([lty, rty], Int, Float)
        elif any([isinstance(n.op, op) for op in [ast.BitOr, ast.BitAnd, ast.BitXor]]):
            ty = ty_join([lty, rty], Bool, Int)
        elif any([isinstance(n.op, op) for op in [ast.LShift, ast.RShift]]):
            ty = ty_join([lty, rty], Int, Int)

        return (node, ty)

    def visitUnaryOp(self, n, env):
        (operand, ty) = self.dispatch(n.operand, env)
        node = ast.UnaryOp(op=n.op, operand=operand)
        if isinstance(n.op, ast.Invert):
            ty = prim_join([ty], Int, Int)
        elif any([isinstance(n.op, op) for op in [ast.UAdd, ast.USub]]):
            ty = prim_join([ty])
        elif isinstance(op, ast.Not):
            ty = Bool
        return (node, ty)

    def visitCompare(self, n, env):
        (left, _) = self.dispatch(n.left, env)
        comparators = [comp for (comp, _) in [self.dispatch(ocomp, env) for ocomp in n.comparators]]
        return (ast.Compare(left=left, ops=n.ops, comparators=comparators), Bool)

    # Collections stuff    
    def visitList(self, n, env):
        if isinstance(n.ctx, ast.Store):
            return self.visitTuple(n, env)
        eltdata = [self.dispatch(x, env) for x in n.elts]
        elttys = [ty for (elt, ty) in eltdata]
        ty = tyjoin(elttys)
        elts = [elt for (elt, ty) in eltdata]
        return (ast.List(elts=elts, ctx=n.ctx), List(ty))

    def visitTuple(self, n, env):
        eltdata = [self.dispatch(x, env) for x in n.elts]
        tys = [ty for (elt, ty) in eltdata]
        elts = [elt for (elt, ty) in eltdata]
        return (ast.Tuple(elts=elts, ctx=n.ctx), Tuple(*tys))

    def visitDict(self, n, env):
        pass

    def visitSet(self, n, env):
        pass

    def visitListComp(self, n, env):
        pass

    def visitSetComp(self, n, env):
        pass

    def visitDictComp(self, n, env):
        pass

    # No idea what this is, can't find anything w/ cursory search
    def visitGeneratorExp(self, n, env):
        pass

    # Control flow stuff
    def visitYield(self, n, env):
        pass

    def visitYieldFrom(self, n, env):
        pass

    def visitIfExp(self, n, env):
        pass

    # Function stuff
    def visitCall(self, n, env):
        def cast_args(argdata, fun, funty):
            if any([tyinstance(funty, x) for x in UNCALLABLES]):
                raise StaticTypeError()
            elif tyinstance(funty, Dyn):
                return ([v for (v, s) in argdata],
                        cast(fun, Dyn, Function([s for (v, s) in argdata], Dyn), 
                             "Function of incorrect type"),
                        Dyn)
            elif tyinstance(funty, Function):
                if len(argdata) >= len(funty.froms):
                    args = [cast(v, s, t, "Argument of incorrect type") for ((v, s), t) in 
                            zip(argdata, funty.froms)]
                    return (args, fun, funty.to)
                else: raise StaticTypeError() 
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
        call = agnostic_cast(call, ret, "Return value of incorrect type")
        return (call, ret)

    def visitLambda(self, n, env):
        pass

    # Variable stuff
    def visitName(self, n, env):
        try:
            ty = env[n.id]
            if isinstance(n.ctx, ast.Delete) and not tyinstance(ty, Dyn):
                raise StaticTypeError('Attempting to delete statically typed id')
        except KeyError:
            ty = Dyn
        return (n, ty)

    def visitAttribute(self, n, env):
        pass

    def visitSubscript(self, n, env):
        pass

    def visitStarred(self, n, env):
        pass

    # Literal stuff
    def visitNum(self, n, env):
        ty = Dyn
        v = n.n
        if type(v) == int:
            ty = Int
        elif type(v) == float:
            ty = Float
        elif type(v) == complex:
            ty = Complex
        return (n, ty)

    def visitStr(self, n, env):
        return (n, String)

    def visitBytes(self, n, env):
        pass

    def visitEllipsis(self, n, env):
        pass


# Probably gargbage
def make_static_instances(root):
    for n in ast.walk(root):
        if isinstance(n, ast.FunctionDef):
            for arg in n.args.args:
                if isinstance(arg.annotation, ast.Call) and \
                        isinstance(arg.annotation.func, ast.Name):
                    if arg.annotation.func.id == Instance.__name__:
                        arg.annotation.func.id = InstanceStatic.__name__
                        arg.annotation.args[0] = ast.Str(s=arg.annotation.args[0].id)
                    elif arg.annotation.func.id == Class.__name__:
                        arg.annotation.func.id = ClassStatic.__name__
                        arg.annotation.args[0] = ast.Str(s=arg.annotation.args[0].id)
                elif isinstance(arg.annotation, ast.Name) and \
                        not arg.annotation.id in [cls.__name__ for cls in PyType.__subclasses__()] and \
                        not arg.annotation.id in [cls.builtin.__name__ for cls in PyType.__subclasses__() if \
                                                      hasattr(cls, 'builtin') and cls.builtin]:
                    arg.annotation = ast.Call(func=ast.Name(id=InstanceStatic.__name__, ctx=arg.annotation.ctx),
                                              args=[ast.Str(s=arg.annotation.id)])
    return n

def make_dynamic_instances(root):
    for n in ast.walk(root):
        if isinstance(n, ast.FunctionDef):
            for arg in n.args.args:
                if isinstance(arg.annotation, ast.Call) and \
                        isinstance(arg.annotation.func, ast.Name):
                    if arg.annotation.func.id == InstanceStatic.__name__:
                        arg.annotation.func.id = Instance.__name__
                        arg.annotation.args[0] = ast.Name(id=arg.annotation.args[0].id, ctx=ast.Load())
                    elif arg.annotation.func.id == ClassStatic.__name__:
                        arg.annotation.func.id = Class.__name__
                        arg.annotation.args[0] = ast.Name(id=arg.annotation.args[0].id, ctx=ast.Load())
    return n
