import ast, typing, flags
from vis import Visitor
from visitors import DictGatheringVisitor, GatheringVisitor, SetGatheringVisitor
from typing import *
from relations import *
from exc import StaticTypeError
from gatherers import Classfinder, Killfinder, Aliasfinder
from importer import ImportFinder

def lift(vs):
    nvs = {}
    for m in vs:
        if isinstance(m, Var):
            nvs[m.var] = vs[m]
    return nvs

def typeparse(tyast, classes):
    module = ast.Module(body=[ast.Assign(targets=[ast.Name(id='ty', ctx=ast.Store())], value=tyast)])
    module = ast.fix_missing_locations(module)
    code = compile(module, '<string>', 'exec')
    locs = {}
    globs = classes.copy()
    globs.update(typing.__dict__)
    exec(code, globs, locs)
    return normalize(locs['ty'])

def update(add, defs, constants={}):
    for x in add:
        if x not in constants:
            if x not in defs:
                defs[x] = add[x]
            else: defs[x] = tymeet([add[x], defs[x]])
        elif not subcompat(add[x], constants[x]):
            raise StaticTypeError('Bad assignment')

class Typefinder(DictGatheringVisitor):
    examine_functions = False

    classfinder = Classfinder()
    killfinder = Killfinder()
    aliasfinder = Aliasfinder()
    importer = ImportFinder()

    def dispatch_scope(self, n, env, constants, tyenv=None, type_inference=True):
        self.vartype = typing.Bottom if type_inference else typing.Dyn
        if tyenv == None:
            tyenv = {}
        if not hasattr(self, 'visitor'): # preorder may not have been called
            self.visitor = self
            
        imported = self.importer.dispatch_statements(n)

        class_aliases = self.classfinder.dispatch_statements(n)
        class_aliases.update(tyenv)
        externals = self.killfinder.dispatch_statements(n)

        defs = imported.copy()
        alias_map = {}
        
        for s in n:
            add = self.dispatch(s, class_aliases)
            update(add, defs, constants)

        alias_map = self.aliasfinder.dispatch_statements(n, defs)

        orig_map = alias_map.copy()
        while True:
            new_map = alias_map.copy()
            for alias1 in new_map:
                for alias2 in orig_map:
                    if alias1 == alias2:
                        continue
                    else:
                        new_map[alias1] = new_map[alias1].copy().substitute_alias(alias2, orig_map[alias2].copy())
            if new_map == alias_map:
                break
            else: alias_map = new_map
        # De-alias
        for var in defs:
            for alias in new_map:
                defs[var] = defs[var].substitute_alias(alias, new_map[alias])

        for k in externals:
            if k in defs:
                if x in env and normalize(defs[x]) != normalize(env[x]):
                    raise StaticTypeError('Global assignment of incorrect type')
                else:
                    del defs[x]
                    del indefs[x]

        indefs = constants.copy()
        indefs.update(defs)
        # export aliases
        indefs.update({TypeVariable(k):new_map[k] for k in new_map})
        return indefs, defs
            
    def combine_expr(self, s1, s2):
        s2.update(s1)
        return s2

    def combine_stmt(self, s1, s2):
        update(s1, s2)
        return s2

    def combine_stmt_expr(self, stmt, expr):
        update(stmt, expr)
        return expr
    
    def default_expr(self, n, aliases):
        return {}
    def default_stmt(self, *k):
        return {}

    def visitAssign(self, n, aliases):
        vty = self.vartype
        env = {}
        for t in n.targets:
            env.update(self.dispatch(t, vty))
        return env

    def visitFor(self, n, aliases):
        vty = self.vartype
        env = self.dispatch(n.target, vty)
        uenv = super(Typefinder, self).visitFor(n, aliases)
        update(uenv, env)
        return env

    def visitFunctionDef(self, n, aliases):
        annoty = None
        for dec in n.decorator_list:
            if is_annotation(dec):
                annoty = typeparse(dec.args[0], aliases)
        argtys = []
        argnames = []
        for arg in n.args.args:
            if flags.PY_VERSION == 3:
                argnames.append(arg.arg)
            else: argnames.append(arg.id)
            if flags.PY_VERSION == 3 and arg.annotation:
                argtys.append(typeparse(arg.annotation, aliases))
            else: argtys.append(Dyn)
        if flags.PY_VERSION == 3 and n.returns:
            ret = typeparse(n.returns, aliases)
        else: ret = Dyn
        ty = Function(argtys, ret)
        if annoty:
            if subcompat(ty, annoty):
                return {Var(n.name): annoty}
            else: raise StaticTypeError('Annotated type does not match type of function (%s </~ %s)' % (ty, annoty))
        else:
            return {Var(n.name): ty}

    def visitClassDef(self, n, aliases):
        def_finder = Typefinder()
        internal_aliases = aliases.copy()
        internal_aliases.update({n.name:TypeVariable(n.name), 'Self':Self()})
        _, defs = def_finder.dispatch_scope(n.body, {}, {}, internal_aliases, type_inference=False)
        ndefs = {}
        for m in defs:
            if isinstance(m, Var):
                ndefs[m.var] = defs[m]
        cls = Class(n.name, ndefs)
        return {Var(n.name): cls}
        
    def visitName(self, n, vty):
        if isinstance(n.ctx, ast.Store):
            return {Var(n.id): vty}
        else: return {}

    def visitTuple(self, n, vty):
        env = {}
        if isinstance(n.ctx, ast.Store):
            if tyinstance(vty, Dyn):
                [env.update(self.dispatch(t, Dyn)) for t in n.elts]
            elif tyinstance(vty, Bottom):
                [env.update(self.dispatch(t, Bottom)) for t in n.elts]
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

    def visitWith(self, n, aliases):
        vty = Dyn
        env = self.dispatch(n.optional_vars, vty) if n.optional_vars else {}
        with_env = self.dispatch_statements(n.body, aliases)
        update(with_env, env)
        return env

    def visitExceptHandler(self, n, aliases):
        vty = Dyn
        if n.name:
            if flags.PY_VERSION == 3:
                env = {Var(n.name): vty}
            elif flags.PY_VERSION == 2:
                env = self.dispatch(n.name, Dyn)
        else:
            env = {}
        b_env = self.dispatch_statements(n.body, aliases)
        update(b_env, env)
        return env

