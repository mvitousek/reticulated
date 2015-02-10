import ast, typing, flags
from vis import Visitor
from visitors import DictGatheringVisitor, GatheringVisitor, SetGatheringVisitor
from typing import *
from relations import *
from exc import StaticTypeError
from errors import errmsg
from gatherers import ClassDynamizationVisitor
import static

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

def update(add, defs, constants={}, location=None, file=None):
    for x in add:
        if x not in constants:
            if x not in defs:
                defs[x] = add[x]
            else:
                defs[x] = tyjoin([add[x], defs[x]])
        elif flags.FINAL_PARAMETERS:
            if not subcompat(add[x], constants[x]):
                raise StaticTypeError(errmsg('BAD_DEFINITION', file, location, x, constants[x], add[x]))
        elif x not in defs:
            defs[x] = tyjoin([add[x], constants[x]])
        else:
            defs[x] = tyjoin([add[x], constants[x], defs[x]])

class Typefinder(DictGatheringVisitor):
    examine_functions = False
    filename = 'dummy'

    def combine_expr(self, s1, s2):
        s2.update(s1)
        return s2

    def combine_stmt(self, s1, s2):
        if flags.JOIN_BRANCHES:
            update(s1, s2, location=s1, file=self.filename)
        else: 
            s2 = {k:s2[k] if k in s1 else Dyn for k in s2}
            s1 = {k:s1[k] if k in s2 else Dyn for k in s1}
            update(s1,s2, location=s1, file=self.filename)
        return s2

    def combine_stmt_expr(self, stmt, expr):
        update(stmt, expr, location=stmt, file=self.filename)
        return expr
    
    def default_expr(self, n, *args):
        return {}
    def default_stmt(self, *k):
        return {}

    def visitAssign(self, n, *args):
        return self.default_stmt()

    def visitAugAssign(self, n, *args):
        return self.default_stmt()

    def visitFor(self, n, *args):
        return self.default_stmt()

    def visitFunctionDef(self, n, vty, aliases):
        annoty = None
        infer = flags.TYPED_SHAPES
        separate = False
        sepfrom = DynParameters
        septo = Dyn
        for dec in n.decorator_list:
            if is_annotation(dec):
                annoty = typeparse(dec.args[0], aliases)
            elif is_annotation(dec):
                annoty = typeparse(dec.args[0], aliases)
            elif isinstance(dec, ast.Name) and dec.id == 'retic_noinfer':
                infer = False
            elif isinstance(dec, ast.Name) and dec.id == 'retic_infer':
                infer = True
            elif isinstance(dec, ast.Name) and dec.id == 'parameters':
                separate = True
                sepfrom = AnonymousParameters([typeparse(x, aliases) for x in dec.args])
            elif isinstance(dec, ast.Name) and dec.id == 'returns':
                separate = True
                septo = typeparse(dec.args[0], aliases)
            else: return {Var(n.name): Dyn}

        if separate:
            annoty = Function(sepfrom, septo)

        if not infer:
            return {Var(n.name): Dyn}

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
                    argannot = typeparse(arg.annotation, aliases)
                    argtys.append((arg_id, argannot))
                else: argtys.append((arg_id, Dyn))
            ffrom = NamedParameters(argtys)
        ty = Function(ffrom, ret)
        if annoty:
            if info_join(ty, annoty).top_free():
                return {Var(n.name): annoty}
            else: raise StaticTypeError('Annotated type does not match type of function (%s </~ %s)' % (ty, annoty))
        else:
            return {Var(n.name): ty}

    def visitClassDef(self, n, vty, aliases):
        infer = flags.TYPED_SHAPES
        efields = {}
        emems = {}
        for dec in n.decorator_list:
            if isinstance(dec, ast.Name) and dec.id == 'noinfer':
                infer = False
            elif isinstance(dec, ast.Name) and dec.id == 'infer':
                infer = True
            elif isinstance(dec, ast.Call) and isinstance(dec.func, ast.Name) and \
                 dec.func.id == 'fields' and \
                 all(isinstance(k, ast.Str) for k in dec.args[0].keys):
                fields = {a.s: typeparse(b, aliases) for a,b in zip(dec.args[0].keys, dec.args[0].values)}
                efields.update(fields) 
                deftype = Class(n.name, {}, efields)
            elif isinstance(dec, ast.Call) and isinstance(dec.func, ast.Name) and \
                 dec.func.id == 'members' and \
                 all(isinstance(k, ast.Str) for k in dec.args[0].keys):
                fields = {a.s: typeparse(b, aliases) for a,b in zip(dec.args[0].keys, dec.args[0].values)}
                emems.update(fields) 
            else: return {Var(n.name): Dyn}

        if efields or emems:
            deftype = Class(n.name, emems, efields)
        else: deftype = Dyn

        if not infer:
            return {Var(n.name): deftype}

        internal_aliases = aliases.copy()
        internal_aliases.update({n.name:TypeVariable(n.name), 'Self':Self()})
    #    _, defs = static.typecheck(n.body, '', 0, internal_aliases, inference_enabled=False)

        defs = static.classtypes(n.body, internal_aliases, static.Misc())
        if ClassDynamizationVisitor().dispatch_statements(n.body):
            return {Var(n.name): deftype}

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
        ndefs = emems
        for m in defs:
            if isinstance(m, Var) and (m.var[:1] != '_' or m.var[-2:] == '__') and\
                    m.var in class_members:
                if tyinstance(defs[m], Class):
                    ndefs[m.var] = Dyn
                else: ndefs[m.var] = defs[m]
        cls = Class(n.name, ndefs, efields)
        return {Var(n.name): cls}
        
    def visitName(self, n, vty, aliases):
        if isinstance(n.ctx, ast.Store) and vty:
            return {Var(n.id): Dyn}
        else: return {}

    def visitcomprehension(self, n, vty, aliases):
        iter = self.dispatch(n.iter, vty, aliases)
        ifs = self.reduce_expr(n.ifs, vty, aliases)
        if flags.PY_VERSION == 2 and vty:
            target = self.dispatch(n.target, True, aliases)
        else: target = {}
        return self.combine_expr(self.combine_expr(iter, ifs), target)

    def visitTuple(self, n, vty, aliases):
        env = {}
        if isinstance(n.ctx, ast.Store) and vty:
            [env.update(self.dispatch(t, vty, aliases)) for t in n.els]
        return env

    def visitList(self, n, vty, aliases):
        if isinstance(n.ctx, ast.Store):
            return self.visitTuple(n, vty)
        else: return {}

    def visitWith(self, n, vty, aliases):
        if flags.PY_VERSION == 3 and flags.PY3_VERSION >= 3:
            env = {}
            for item in n.items:
                update(self.dispatch(item, True, aliases), env, location=n, file=self.filename)
        else:
            env = self.dispatch(n.optional_vars, True, aliases) if n.optional_vars else {}
        with_env = self.dispatch(n.body, vty, aliases)
        update(with_env, env, location=n, file=self.filename)
        return env

    def visitwithitem(self, n, vty, aliases):
        return self.dispatch(n.optional_vars, vty, aliases) if n.optional_vars else {}

    def visitExceptHandler(self, n, vty, aliases):
        if n.name:
            if flags.PY_VERSION == 3:
                env = {Var(n.name): Dyn}
            elif flags.PY_VERSION == 2:
                env = self.dispatch(n.name, True, aliases)
        else:
            env = {}
        b_env = self.dispatch(n.body, vty, aliases)
        update(b_env, env, location=n, file=self.filename)
        return env
