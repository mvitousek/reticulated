import ast, typing, flags
from vis import Visitor
from typing import *
from relations import *
from exc import StaticTypeError

def typeparse(tyast):
    module = ast.Module(body=[ast.Assign(targets=[ast.Name(id='ty', ctx=ast.Store())], value=tyast)])
    module = ast.fix_missing_locations(module)
    code = compile(module, '<string>', 'exec')
    locs = {}
    exec(code, typing.__dict__, locs)
    return normalize(locs['ty'])

def update(add, defs, constants={}):
    for x in add:
        if x not in defs:
            defs[x] = add[x]
        elif x not in constants:
            defs[x] = tymeet([add[x], defs[x]])
        elif not subcompat(add[x], defs[x]):
            raise StaticTypeError('Bad assignment')
            

class Typefinder(Visitor):
    def dispatch_scope(self, n, env, initial_locals={}):
        if not hasattr(self, 'visitor'): # preorder may not have been called
            self.visitor = self
        defs = initial_locals.copy()
        globs = set([])
        locals = set([])
        for s in n:
            add, kill = self.dispatch(s)
            update(add, defs, initial_locals)
            locals.update(set(add.keys()) - set(initial_locals.keys()))
            globs.update(kill)
        for x in globs:
            if x in defs:
                if x in env and normalize(defs[x]) != normalize(env[x]):
                    raise StaticTypeError('Global assignment of incorrect type')
                else:
                    del defs[x]
                    locals.remove(x)
        return defs, locals

    def dispatch_statements(self, n):
        if not hasattr(self, 'visitor'): # preorder may not have been called
            self.visitor = self
        defs = {}
        globs = {}
        for s in n:
            (add, kill) = self.dispatch(s)
            update(add, defs)
            globs.update(kill)
        return (defs, globs)

    def default(self, n, *args):
        if isinstance(n, ast.stmt):
            return ({}, set([]))
        elif isinstance(n, ast.expr):
            return {}

    def visitAssign(self, n):
        vty = Bottom
        env = {}
        for t in n.targets:
            env.update(self.dispatch(t, vty))
        return (env, set([]))

    def visitIf(self, n):
        vty = Dyn
        (body_env, body_kill) = self.dispatch_statements(n.body)
        (else_env, else_kill) = self.dispatch_statements(n.orelse)
        update(else_env, body_env)
        body_kill.update(else_kill)
        return (body_env, body_kill)

    def visitFor(self, n):
        vty = Bottom
        env = self.dispatch(n.target, vty)
        (for_env, for_kill) = self.dispatch_statements(n.body)
        (else_env, else_kill) = self.dispatch_statements(n.orelse)
        update(for_env, env)
        update(else_env, env)
        for_kill.update(else_kill)
        return (env, for_kill)

    def visitFunctionDef(self, n):
        annoty = None
        for dec in n.decorator_list:
            if is_annotation(dec):
                annoty = typeparse(dec.args[0])
        argtys = []
        argnames = []
        for arg in n.args.args:
            if flags.PY_VERSION == 3:
                argnames.append(arg.arg)
            else: argnames.append(arg.id)
            if flags.PY_VERSION == 3 and arg.annotation:
                argtys.append(typeparse(arg.annotation))
            else: argtys.append(Dyn)
        if flags.PY_VERSION == 3 and n.returns:
            ret = typeparse(n.returns)
        else: ret = Dyn
        ty = Function(argtys, ret)
        if annoty:
            if subcompat(ty, annoty):
                return ({n.name: annoty}, set([]))
            else: raise StaticTypeError('Annotated type does not match type of function (%s </~ %s)' % (ty, annoty))
        else:
            return ({n.name: ty}, set([]))

    def visitClassDef(self, n):
        return {n.name: Dyn}, set([])
        
    def visitName(self, n, vty):
        if isinstance(n.ctx, ast.Store):
            return {n.id: vty}
        else: return {}

    def visitTuple(self, n, vty):
        env = {}
        if isinstance(n.ctx, ast.Store):
            if tyinstance(vty, Dyn):
                [env.update(self.dispatch(t, Dyn)) for t in n.elts]
            elif tyinstance(vty, List):
                [env.update(self.dispatch(t, vty.type)) for t in n.elts]
            elif tyinstance(vty, Dict):
                [env.update(self.dispatch(t, vty.keys)) for t in n.elts]
            elif tyinstance(vty, Tuple) and len(vty.elements) == len(n.elts):
                [env.update(self.dispatch(t, ty)) for (t, ty) in zip(n.elts, vty.elements)]
        return env

    def visitList(self, n, vty):
        if isinstance(n.ctx, ast.Store):
            return self.visitTuple(n, vty)
        else: return {}

    def visitWith(self, n):
        vty = Dyn
        env = self.dispatch(n.optional_vars, vty) if n.optional_vars else {}
        (with_env, kill) = self.dispatch_statements(n.body)
        update(with_env, env)
        return (env, kill)

    def visitTryExcept(self, n):
        env = {}
        kill = set([])
        for handler in n.handlers:
            (hand_env, hand_kill) = self.dispatch(handler)
            update(hand_env, env)
            kill.update(hand_kill)
        (else_env, else_kill) = self.dispatch_statements(n.orelse)
        update(else_env, env)
        kill.update(else_kill)
        return (env, kill)

    def visitTryFinally(self, n):
        (b_env, b_kill) = self.dispatch_statements(n.body)
        (f_env, f_kill) = self.dispatch_statements(n.finalbody)
        update(b_env, f_env)
        f_kill.update(b_kill)
        return (f_env, f_kill)

    def visitTry(self, n):
        env = {}
        kill = set([])
        for handler in n.handlers:
            (hand_env, hand_kill) = self.dispatch(handler)
            update(hand_env, env)
            kill.update(hand_kill)
        (else_env, else_kill) = self.dispatch_statements(n.orelse)
        update(else_env, env)
        kill.update(else_kill)
        (f_env, f_kill) = self.dispatch_statements(n.finalbody)
        update(f_env, env)
        kill.update(f_kill)
        return (env, kill)

    def visitExceptHandler(self, n):
        vty = Dyn
        if n.name:
            if flags.PY_VERSION == 3:
                env = {n.name: vty}
            elif flags.PY_VERSION == 2:
                env = self.dispatch(n.name, Dyn)
        else:
            env = {}
        (b_env, kill) = self.dispatch_statements(n.body)
        update(b_env, env)
        return (env, kill)

    def visitGlobal(self, n):
        return ({}, set(n.names))

    def visitNonlocal(self, n):
        return ({}, set(n.names))

