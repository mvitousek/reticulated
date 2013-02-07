import ast
from vis import Visitor
from typefinder import Typefinder
from typing import *
from relations import *
import typing

DEBUG = False

def warn(msg):
    if DEBUG:
        print('WARNING:', msg)

def uniquify(name, count=[0]):
    count[0] = count[0]+1
    return (ast.Name(id=('@%s%d' % (name, count[0])), ctx=ast.Store()),
            ast.Name(id=('@%s%d' % (name, count[0])), ctx=ast.Load()))

def let(val, ss):
    if isinstance(val, ast.Name):
        return (val, ss)
    else:
        (nstore, nval) = uniquify('letval')
        ss = ss + [ast.Assign(targets=[nstore], value=val)]
        return (nval, ss)

def check(val, ty, line):
    warn('inserting check: %s : %s'  % (ast.dump(val), ast.dump(ty.to_ast())))
    msg = 'value %s does not have type %s' % (ast.dump(val), ast.dump(ty.to_ast()))
    return ast.Assert(test=ast.Call(func=ast.Name(id='has_type', ctx=ast.Load()), args=[val, ty.to_ast()], 
                            keywords=[], starargs=None, kwargs=None), msg=ast.Str(s=msg), lineno=line)

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

class Typechecker(Visitor):
    typefinder = Typefinder()
    
    def dispatch_debug(self, tree, *args):
        ret = super().dispatch(tree, *args)
        print('results of %s' % tree.__class__.__name__)
        if isinstance(ret, tuple):
            if isinstance(ret[0], list):
                [print(ast.dump(x)) for x in ret[0]]
            if isinstance(ret[1], list):
                [print(ast.dump(x)) for x in ret[1]]
            if isinstance(ret[1], ast.AST):
                print(ast.dump(ret[1]))
        if isinstance(ret, ast.AST):
            print(ast.dump(ret))
        return ret

    if DEBUG:
        dispatch = dispatch_debug

    def typecheck(self, n):
        n = self.preorder(n, {})
        n = ast.fix_missing_locations(n)
        return n

    def dispatch_statements(self, n, env):
        env = env.copy()
        env.update(self.typefinder.dispatch_statements(n))
        ret = Void
        body = []
        for s in n:
            (stmts, ty) = self.dispatch(s, env)
            body += stmts
            ret = ty
        return (body, ret)
        
    def visitModule(self, n, env):
        (body, ty) = self.dispatch_statements(n.body, env)
        return ast.Module(body=body)

## STATEMENTS ##

    def visitImport(self, n, env):
        return ([n], Void)

    def visitImportFrom(self, n, env):
        return ([n], Void)
    
    def visitFunctionDef(self, n, env): #TODO: check defaults, handle varargs and kwargs
        argnames = []
        for arg in n.args.args:
            argnames.append(arg.arg)
        nty = env[n.name]
        env = env.copy()
        env.update(dict(zip(argnames, nty.froms)))
        (body, ty) = self.dispatch_statements(n.body, env)
        if not tycompat(ty, nty.to):
            raise StaticTypeError()
        if not 'typed' in [x.id for x in n.decorator_list]:
            decorator_list = n.decorator_list + [ast.Name(id='typed', ctx=ast.Load(), lineno=n.lineno)]
        else: decorator_list = n.decorator_list
        return ([ast.FunctionDef(name=n.name, args=n.args,
                                 body=body, decorator_list=decorator_list,
                                 returns=n.returns)], Void)

    def visitReturn(self, n, env):
        (value, ty, ss) = self.dispatch(n.value, env) if n.value else (None, Void, [])
        return (ss + [ast.Return(value=value)], ty)

    def visitDelete(self, n, env):
        targets = []
        ss = []
        for t in n.targets:
            (value, ty, s) = self.dispatch(t, env)
            ss += s
#            if not tyinstance(ty, Dyn): should be handled when seeing Del()
#                raise StaticTypeError()
            targets.append(value)
        return (ss + [ast.Delete(targets=targets)], Void)

    def visitAssign(self, n, env):
        (val, vty, ssf) = self.dispatch(n.value, env)
        targets = []
        ss = []
        for target in n.targets:
            (ntarget, tty, nss) = self.dispatch(target, env)
            warn('assigning value of type %s to target of type %s' % (ast.dump(vty.to_ast()), ast.dump(tty.to_ast())))
            if vty != tty and not tyinstance(tty, Dyn):
                if tycompat(vty, tty):
                    (val, ssf) = let(val, ssf)
                    ssf.append(check(val, tty, n.lineno))
                else:
                    raise StaticTypeError()
            targets.append(ntarget)
            ss += nss
        return (ss + ssf + [ast.Assign(targets=targets, value=val)], Void)

    def visitExpr(self, n, env):
        (value, ty, ss) = self.dispatch(n.value, env)
        return (ss + [ast.Expr(value=value)], Void)

### EXPRESSIONS ###

    # Note that we do not insert runtime checks on arguments, because
    # we assume that the callee is decorated with @typed
    def visitCall(self, n, env):
        def test_call(funty, atys):
            if any([tyinstance(funty, x) for x in UNCALLABLES]):
                raise StaticTypeError()
            elif tyinstance(funty, Function):
                if not (len(funty.froms) <= len(atys) and \
                            all([tycompat(aty, fty) for (aty, fty) in zip(atys, funty.froms)])):
                    raise StaticTypeError()
                return funty.to
            elif tyinstance(funty, ClassStatic):
                return InstanceStatic(funty.klass_name)
            elif tyinstance(funty, Object):
                if '__call__' in ty.members:
                    funty = funty.members['__call__']
                    return test_call(funty, atys)
                else: return Dyn
            else: return Dyn

        (func, ty, ss) = self.dispatch(n.func, env)
        argdata = [self.dispatch(x, env) for x in n.args]
        args = []
        atys = []
        for (arg, aty, ass) in argdata:
            ss += ass
            args.append(arg)
            atys.append(aty)
        ret = test_call(ty, atys)
        return (ast.Call(func=func, args=args, keywords=n.keywords,
                        starargs=n.starargs, kwargs=n.kwargs), ret, ss)
            
    def visitName(self, n, env):
        try:
            ty = env[n.id]
            if isinstance(n.ctx, ast.Delete):
                raise StaticTypeError()
        except KeyError:
            ty = Dyn
        return (n, ty, [])

    def visitNum(self, n, env):
        ty = Dyn
        v = n.n
        if type(v) == int:
            ty = Int
        elif type(v) == float:
            ty = Float
        elif type(v) == complex:
            ty = Complex
        return (n, ty, [])

    def visitStr(self, n, env):
        return (n, String, [])

    def visitList(self, n, env):
        if isinstance(n.ctx, ast.Store):
            return self.visitTuple(n, env)
        eltdata = [self.dispatch(x, env) for x in n.elts]
        elttys = [ty for (elt, ty, s) in eltdata]
        ty = tyjoin(elttys)
        ss = sum([s for (elt, ty, s) in eltdata], [])
        elts = [elt for (elt, ty, s) in eltdata]
        return (ast.List(elts=elts, ctx=n.ctx), List(ty), ss)

    def visitTuple(self, n, env):
        eltdata = [self.dispatch(x, env) for x in n.elts]
        tys = [ty for (elt, ty, s) in eltdata]
        ss = sum([s for (elt, ty, s) in eltdata], [])
        elts = [elt for (elt, ty, s) in eltdata]
        return (ast.Tuple(elts=elts, ctx=n.ctx), Tuple(*tys), ss)
