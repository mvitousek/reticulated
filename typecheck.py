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

def warn(msg):
    if PRINT_WARNINGS:
        print('WARNING:', msg)

def cast(val, src, trg, msg, cast_function='cast'):
    src = normalize(src)
    trg = normalize(trg)
    
    if not tycompat(src, trg):
        raise StaticTypeError("%s: cannot cast from %s to %s (line %d)" % (msg, src, trg, val.lineno))
    elif src == trg:
        return val
    elif not OPTIMIZED_INSERTION:
        return ast.Call(func=ast.Name(id=cast_function, ctx=ast.Load()),
                        args=[val, src.to_ast(), trg.to_ast(), ast.Str(s=msg)],
                        keywords=[], starargs=None, kwargs=None)
    else:
        # Specialized version that omits unnecessary casts depending what mode we're in,
        # e.g. cast-as-assert would omit naive upcasts
        pass

# Casting with unknown source type, as in cast-as-assertion 
# function return values at call site
def agnostic_cast(val, trg, msg, cast_function='check'):
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
        print('results of %s' % tree.__class__.__name__)
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

    def dispatch_statements(self, n, env, ret):
        env = env.copy()
        env.update(self.typefinder.dispatch_statements(n))
        body = []
        for s in n:
            (stmt, ty) = self.dispatch(s, env, ret)
            body.append(stmt)
        return (body, ty)
        
    def visitModule(self, n, env):
        (body, ty) = self.dispatch_statements(n.body, env, Void)
        return ast.Module(body=body)

## STATEMENTS ##
    def visitImport(self, n, env, ret):
        return (n, Void)

    def visitImportFrom(self, n, env, ret):
        return (n, Void)
    
    def visitFunctionDef(self, n, env, ret): #TODO: check defaults, handle varargs and kwargs
        argnames = []
        for arg in n.args.args:
            argnames.append(arg.arg)
        nty = env[n.name]
        
        env = env.copy()
        env.update(dict(zip(argnames, nty.froms)))
        
        (body, ty) = self.dispatch_statements(n.body, env, nty.to)
        return (ast.FunctionDef(name=n.name, args=n.args,
                                 body=body, decorator_list=n.decorator_list,
                                 returns=n.returns, lineno=n.lineno), Void)

    def visitReturn(self, n, env, ret):
        (value, ty) = self.dispatch(n.value, env) if n.value else (None, Void)
        value = cast(value, ty, ret, "Return value of incorrect type")
        return (ast.Return(value=value, lineno=n.lineno), ret)

    def visitDelete(self, n, env, ret):
        targets = []
        for t in n.targets:
            (value, ty) = self.dispatch(t, env)
            targets.append(value)
        return (ast.Delete(targets=targets, lineno=n.lineno), Void)

    def visitAssign(self, n, env, ret):
        (val, vty) = self.dispatch(n.value, env)
        targets = []
        for target in n.targets:
            (ntarget, tty) = self.dispatch(target, env)
            warn('assigning value of type %s to target of type %s' % (ast.dump(vty.to_ast()), ast.dump(tty.to_ast())))
            val = cast(val, vty, tty, "Assignee of incorrect type")
            targets.append(ntarget)
        return (ast.Assign(targets=targets, value=val, lineno=n.lineno), Void)

    def visitExpr(self, n, env, ret):
        (value, ty) = self.dispatch(n.value, env)
        return (ast.Expr(value=value, lineno=n.lineno), Void)

### EXPRESSIONS ###

    def visitCall(self, n, env):
        def cast_args(argdata, funty):
            if any([tyinstance(funty, x) for x in UNCALLABLES]):
                raise StaticTypeError()
            
            elif tyinstance(funty, Function):
                if len(argdata) >= len(funty.froms):
                    args = [cast(v, s, t, "Argument of incorrect type") for ((v, s), t) in 
                            zip(argdata, funty.froms)]
                    return (args, funty.to)
                else: raise StaticTypeError() 
            elif tyinstance(funty, Object):
                if '__call__' in ty.members:
                    funty = funty.members['__call__']
                    return cast_args(args, atys, funty)
                else: return ([cast(v, s, Dyn, "Argument of incorrect type") for (v, s) in
                               argdata], Dyn)
            else: return ([cast(v, s, Dyn, "Argument of incorrect type") for (v, s) in
                           argdata], Dyn)

        (func, ty) = self.dispatch(n.func, env)
        argdata = [self.dispatch(x, env) for x in n.args]
        (args, ret) = cast_args(argdata, ty)
        call = ast.Call(func=func, args=args, keywords=n.keywords,
                        starargs=n.starargs, kwargs=n.kwargs)
        call = agnostic_cast(call, ret, "Return value of incorrect type")
        return (call, ret)
            
    def visitName(self, n, env):
        try:
            ty = env[n.id]
            if isinstance(n.ctx, ast.Delete):
                raise StaticTypeError()
        except KeyError:
            ty = Dyn
        return (n, ty)

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
