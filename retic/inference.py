import flags, utils, rtypes
from relations import *
from visitors import GatheringVisitor
from typing import Var, StarImport

class InferVisitor(GatheringVisitor):
    examine_functions = False
    def combine_expr(self, s1, s2):
        return s1 + s2
    combine_stmt = combine_expr
    combine_stmt_expr = combine_expr
    empty_stmt = list
    empty_expr = list
    
    def infer(self, typechecker, locals, initial_locals, ns, env, misc):
        lenv = {}
        env = env.copy()
        new_assignments = []
        while True:
            verbosity = flags.WARNINGS
            flags.WARNINGS = -1
            assignments = self.preorder(ns, env, misc, 
                                        typechecker)
            flags.WARNINGS = verbosity
            while assignments:
                k, v = assignments[0]
                del assignments[0]
                if isinstance(k, ast.Name):
                    new_assignments.append((k,v))
                elif isinstance(k, ast.Tuple) or isinstance(k, ast.List):
                    if tyinstance(v, Tuple):
                        assignments += (list(zip(k.elts, v.elements)))
                    elif tyinstance(v, Iterable) or tyinstance(v, List):
                        assignments += ([(e, v.type) for e in k.elts])
                    elif tyinstance(v, Dict):
                        assignments += (list(zip(k.elts, v.keys)))
                    else: assignments += ([(e, Dyn) for e in k.elts])
            nlenv = {}
            for local in [local for local in locals if local not in initial_locals]:
                if isinstance(local, TypeVariable) or isinstance(local, StarImport):
                    continue
                ltys = [y for x,y in new_assignments if x.id == local.var]
                ty = tyjoin(ltys).lift()
                nlenv[local] = ty
            if nlenv == lenv:
                env.update({Var(k.var): initial_locals[k] for k in initial_locals})
                break
            else:
                env.update(nlenv)
                lenv = nlenv
        return {k:env[k] if not tyinstance(env[k], InferBottom) else Dyn for k in env}
    
    def visitAssign(self, n, env, misc, typechecker):
        _, vty = typechecker.preorder(n.value, env, misc)
        assigns = []
        for target in n.targets:
            ntarget, tty = typechecker.preorder(target, env, misc)
            if not (flags.SEMANTICS == 'MONO' and isinstance(target, ast.Attribute) and \
                        not tyinstance(tty, Dyn)):
                assigns.append((ntarget,vty))
        return assigns
    def visitAugAssign(self, n, env, misc, typechecker):
        optarget = utils.copy_assignee(n.target, ast.Load())

        assignment = ast.Assign(targets=[n.target], 
                                value=ast.BinOp(left=optarget,
                                                op=n.op,
                                                right=n.value,
                                                lineno=n.lineno),
                                lineno=n.lineno)
        return self.dispatch(assignment, env, misc, typechecker)
    def visitFor(self, n, env, misc, typechecker):
        target, _ = typechecker.preorder(n.target, env, misc)
        _, ity = typechecker.preorder(n.iter, env, misc)
        body = self.dispatch_statements(n.body, env, misc, typechecker)
        orelse = self.dispatch_statements(n.orelse, env, misc, typechecker)
        return [(target, utils.iter_type(ity))] + body + orelse
    def visitFunctionDef(self, n, env, misc, typechecker):
        return [(ast.Name(id=n.name, ctx=ast.Store()), env[Var(n.name)])]
    def visitClassDef(self, n, env, misc, typechecker):
        return [(ast.Name(id=n.name, ctx=ast.Store()), env[Var(n.name)])]
    def visitImport(self, n, env, *args):
        return [(ast.Name(id=t.asname if t.asname is not None else t.name, ctx=ast.Store()), env[Var(t.asname if t.asname is not None else t.name)]) for t in n.names]
    def visitImportFrom(self, n, env, *args):
        if '*' in [t.name for t in n.names]:
            impenv = env[StarImport(n.module)]
            return [(ast.Name(id=t.var, ctx=ast.Store()), impenv[t]) for t in impenv if isinstance(t, Var)]
        return [(ast.Name(id=t.asname if t.asname is not None else t.name, ctx=ast.Store()), env[Var(t.asname if t.asname is not None else t.name)]) for t in n.names]
