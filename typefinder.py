import ast, typing, flags
from vis import Visitor
from visitors import DictGatheringVisitor, GatheringVisitor, SetGatheringVisitor
from typing import *
from relations import *
from exc import StaticTypeError
from gatherers import Classfinder, Killfinder, Aliasfinder, Inheritfinder, ClassDynamizationVisitor
from importer import ImportFinder

def lift(vs):
    nvs = {}
    for m in vs:
        if isinstance(m, Var):
            nvs[m.var] = vs[m]
    return nvs

def aliases(env):
    nenv = {}
    for k in env:
        if isinstance(k, TypeVariable):
            nenv[k.name] = env[k]
    return nenv
        
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
            else:
                defs[x] = tyjoin([add[x], defs[x]])
        elif not subcompat(add[x], constants[x]):
            raise StaticTypeError('Bad assignment')

class Typefinder(DictGatheringVisitor):
    examine_functions = False

    classfinder = Classfinder()
    killfinder = Killfinder()
    aliasfinder = Aliasfinder()
    inheritfinder = Inheritfinder()
    importer = ImportFinder()

    def dispatch_scope(self, n, env, constants, import_depth, filename, tyenv=None, type_inference=True):
        assert(isinstance(import_depth, int))
        self.filename = filename
        self.import_depth = import_depth
        self.vartype = typing.Bottom if type_inference else typing.Dyn
        if tyenv == None:
            tyenv = {}
        if not hasattr(self, 'visitor'): # preorder may not have been called
            self.visitor = self
            
        typing.debug('Importing starting in %s' % self.filename, flags.PROC)
        imported = self.importer.dispatch_statements(n, import_depth)
        typing.debug('Importing finished in %s' % self.filename, flags.PROC)

        typing.debug('Alias search started in %s' % self.filename, flags.PROC)
        class_aliases = self.classfinder.dispatch_statements(n)
        typing.debug('Alias search finished in %s' % self.filename, flags.PROC)
        class_aliases.update(tyenv)
        class_aliases.update(aliases(imported))

        typing.debug('Globals search started in %s' % self.filename, flags.PROC)
        externals = self.killfinder.dispatch_statements(n)
        typing.debug('Globals search finished in %s' % self.filename, flags.PROC)

        defs = {}
        indefs = imported.copy()
        indefs.update(constants.copy())
        alias_map = {}
        

        for s in n:
            add = self.dispatch(s, class_aliases)
            update(add, defs, constants)

        typing.debug('Inheritance checking started in %s' % self.filename, flags.PROC)
        inheritance = self.inheritfinder.dispatch_statements(n)
        typing.debug('Inheritance checking finished in %s' % self.filename, flags.PROC)
        subchecks = []
        
        #Transitive closure, credit to stackoverflow user "soulcheck"
        while True:
            new = {(x, w) for x,y in inheritance for z,w in inheritance if y == z}
            new_inherit = inheritance | new
            if new_inherit == inheritance:
                break
            else:
                inheritance = new_inherit
            
        for (cls, supe) in inheritance:
            if Var(cls) in defs and tyinstance(defs[Var(cls)], Class):
                if Var(supe) in defs and supe not in externals:
                    src = defs[Var(supe)]
                elif Var(supe) in env:
                    src = env[Var(supe)]
                else: continue
                if not tyinstance(src, Class):
                    continue
                mems = src.members.copy()
                mems.update(defs[Var(cls)].members)
                defs[Var(cls)].members.clear()
                defs[Var(cls)].members.update(mems)
                subchecks.append((Var(cls), src))
        
        typing.debug('Alias resolution started in %s' % self.filename, flags.PROC)
        alias_map = self.aliasfinder.dispatch_statements(n, defs)
        typing.debug('Alias resolution finished in %s' % self.filename, flags.PROC)

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

        for (var, supty) in subchecks:
            subty = defs[var]
            lenv = env.copy()
            lenv.update(indefs)
            lenv.update(defs)
            lenv.update({TypeVariable(k):new_map[k] for k in new_map})
            if (flags.SUBCLASSES_REQUIRE_SUBTYPING and not subtype(lenv, Bottom(), subty.instance(), supty.instance())) or\
                    (not flags.SUBCLASSES_REQUIRE_SUBTYPING and not subcompat(subty.instance(), supty.instance())):
                raise StaticTypeError('Subclass %s is not a subtype in file %s' % (var.var, filename))

        for k in externals:
            if k in defs:
                if x in env and defs[x] != env[x]:
                    raise StaticTypeError('Global assignment of incorrect type')
                else:
                    del defs[x]
                    del indefs[x]

        indefs.update(defs)
        # export aliases
        indefs.update({TypeVariable(k):new_map[k] for k in new_map})
        return indefs, defs
            
    def combine_expr(self, s1, s2):
        s2.update(s1)
        return s2

    def combine_stmt(self, s1, s2):
        if flags.JOIN_BRANCHES:
            update(s1, s2)
        else: 
            s2 = {k:s2[k] if k in s1 else Dyn for k in s2}
            s1 = {k:s1[k] if k in s2 else Dyn for k in s1}
            update(s1,s2)
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

    def visitAugAssign(self, n, *args):
        vty = self.vartype
        return self.dispatch(n.target, vty)

    def visitFor(self, n, aliases):
        vty = self.vartype
        env = self.dispatch(n.target, vty)

        body = self.dispatch_statements(n.body, aliases)
        orelse = self.dispatch_statements(n.orelse, aliases) if n.orelse else self.empty_stmt()
        uenv = self.combine_stmt(body,orelse)

        update(uenv, env)
        return env

    def visitFunctionDef(self, n, aliases):
        annoty = None
        for dec in n.decorator_list:
            if is_annotation(dec):
                annoty = typeparse(dec.args[0], aliases)
            else: return {Var(n.name): Dyn}
        argtys = []
        argnames = []

        if flags.PY_VERSION == 3 and n.returns:
            ret = typeparse(n.returns, aliases)
        else: ret = Dyn

        if n.args.vararg:
            ffrom = DynParameters
        elif n.args.kwarg:
            ffrom = DynParameters
        elif flags.PY_VERSION == 3 and n.args.kwonlyargs:
            ffrom = DynParameters
        elif n.args.defaults:
            ffrom = DynParameters
        else:
            for arg in n.args.args:
                arg_id = arg.arg if flags.PY_VERSION == 3 else arg.id
                argnames.append(arg_id)
                if flags.PY_VERSION == 3 and arg.annotation:
                    argtys.append((arg_id, typeparse(arg.annotation, aliases)))
                else: argtys.append((arg_id, Dyn))
            ffrom = NamedParameters(argtys)
        ty = Function(ffrom, ret)
        if annoty:
            if tymeet(ty, annoty) != Bottom:
                return {Var(n.name): annoty}
            else: raise StaticTypeError('Annotated type does not match type of function (%s </~ %s)' % (ty, annoty))
        else:
            return {Var(n.name): ty}

    def visitClassDef(self, n, aliases):
        def_finder = Typefinder()
        internal_aliases = aliases.copy()
        internal_aliases.update({n.name:TypeVariable(n.name), 'Self':Self()})
        _, defs = def_finder.dispatch_scope(n.body, {}, {}, self.import_depth, self.filename,
                                            tyenv=internal_aliases, type_inference=False)
        if ClassDynamizationVisitor().dispatch_statements(n.body):
            return {Var(n.name): Dyn}
        ndefs = {}

        assignments = []
        for s in n.body:
            if isinstance(s, ast.Assign):
                assignments += s.targets
            elif isinstance(s, ast.FunctionDef):
                assignments.append(s.name)
            elif isinstance(s, ast.ClassDef):
                assignments.append(s.name)
        class_members = []
        while assignments:
            k = assignments[0]
            del assignments[0]
            if isinstance(k, ast.Name):
                class_members.append(k.id)
            elif isinstance(k, str):
                class_members.append(k)
            elif isinstance(k, ast.Tuple) or isinstance(k, ast.List):
                assignments += k.elts

        for m in defs:
            if isinstance(m, Var) and (m.var[:2] != '__' or m.var[-2:] == '__') and\
                    m.var in class_members:
                ndefs[m.var] = defs[m]
        cls = Class(n.name, ndefs)
        return {Var(n.name): cls}
        
    def visitName(self, n, vty):
        if isinstance(n.ctx, ast.Store):
            return {Var(n.id): vty}
        else: return {}

    def visitcomprehension(self, n, *args):
        iter = self.dispatch(n.iter, *args)
        ifs = self.reduce_expr(n.ifs, *args)
        if flags.PY_VERSION == 2:
            target = self.dispatch(n.target, Dyn)
        else: target = {}
        return self.combine_expr(self.combine_expr(iter, ifs), target)

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
        if flags.PY_VERSION == 3 and flags.PY3_VERSION == 3:
            env = {}
            for item in n.items:
                update(self.dispatch(item, vty), env)
        else:
            env = self.dispatch(n.optional_vars, vty) if n.optional_vars else {}
        with_env = self.dispatch_statements(n.body, aliases)
        update(with_env, env)
        return env

    def visitwithitem(self, n, vty):
        return self.dispatch(n.optional_vars, vty) if n.optional_vars else {}

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

