import ast
from . import typing, flags
from .vis import Visitor
from .visitors import DictGatheringVisitor, GatheringVisitor, SetGatheringVisitor
from .typing import *
from .relations import *
from .exc import StaticTypeError
from .errors import errmsg
from .gatherers import ClassDynamizationVisitor

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
    type = locs['ty']
    if isinstance(type, str):
        type = globs[type]
    return normalize(type)

def update(add, defs, location=None, file=None):
    for x in add:
        if x in defs:
            stronger = info_join(add[x], defs[x])
            if stronger.top_free():
                defs[x] = stronger
            else:
                raise StaticTypeError(errmsg('BAD_DEFINITION', file, x, x, 
                                             add[x], defs[x]))
        else:
            defs[x] = add[x]

class Typefinder(DictGatheringVisitor):
    examine_functions = False

    def preorder(self, n, vty, aliases, misc):
        self.filename = misc.filename
        return super().preorder(n, vty, aliases, misc)

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
        update(stmt, expr, file=self.filename)
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

    def visitFunctionDef(self, n, vty, aliases, misc):
        annoty = None
        infer = flags.TYPED_SHAPES
        separate = False
        sepfrom = DynParameters
        septo = Dyn
        for dec in n.decorator_list:
            if isinstance(dec, ast.Name) and (dec.id == 'retic_typed' or\
                                              dec.id == 'typed'):
                annoty = typeparse(dec.args[0], aliases)
            elif isinstance(dec, ast.Name) and dec.id == 'noinfer':
                infer = False
            elif isinstance(dec, ast.Name) and dec.id == 'infer':
                infer = True
            elif isinstance(dec, ast.Name) and dec.id == 'parameters':
                separate = True
                sepfrom = AnonymousParameters([typeparse(x, aliases) for x in dec.args])
            elif isinstance(dec, ast.Name) and dec.id == 'returns':
                separate = True
                septo = typeparse(dec.args[0], aliases)
            elif isinstance(dec, ast.Name) and dec.id == 'staticmethod':
                return {Var(n.name, n): Dyn}
            else: continue

        if separate:
            annoty = Function(sepfrom, septo)

        if not infer:
            return {Var(n.name, n): Dyn}

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
                if flags.PY_VERSION == 3 and arg.annotation and n.name != '__init__':
                    argannot = typeparse(arg.annotation, aliases)
                    argtys.append((arg_id, argannot))
                else: argtys.append((arg_id, Dyn))
            ffrom = NamedParameters(argtys)
        ty = Function(ffrom, ret)
        
        if annoty:
            if info_join(ty, annoty).top_free():
                return {Var(n.name, n): annoty}
            else: raise StaticTypeError('Annotated type does not match type of function (%s </~ %s)' % (ty, annoty))
        else:
            return {Var(n.name, n): ty}

    def visitClassDef(self, n, vty, aliases, misc):
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
            else: return {Var(n.name, n): Dyn}

        if efields or emems:
            deftype = Class(n.name, emems, efields)
        else: deftype = Dyn

        if not infer:
            return {Var(n.name, n): deftype}

        internal_aliases = aliases.copy()
        selfref = TypeVariable(n.name)
        selfref.Class = TypeVariable(n.name + '.Class')
        internal_aliases.update({n.name:selfref, (n.name + '.Class'):TypeVariable(n.name + '.Class'), 'Self':Self()})

        defs = misc.static.classtypes(n.body, internal_aliases, misc)
        if ClassDynamizationVisitor().dispatch_statements(n.body):
            return {Var(n.name, n): deftype}

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
        return {Var(n.name, n): cls}
        
    def visitName(self, n, vty, aliases, misc):
        if isinstance(n.ctx, ast.Store) and vty:
            return {Var(n.id, n): Dyn}
        else: return {}

    def visitcomprehension(self, n, vty, aliases, misc):
        iter = self.dispatch(n.iter, vty, aliases, misc)
        ifs = self.reduce_expr(n.ifs, vty, aliases, misc)
        if flags.PY_VERSION == 2 and vty:
            target = self.dispatch(n.target, True, aliases, misc)
        else: target = {}
        return self.combine_expr(self.combine_expr(iter, ifs), target)

    def visitTuple(self, n, vty, aliases, misc):
        env = {}
        if isinstance(n.ctx, ast.Store) and vty:
            [env.update(self.dispatch(t, vty, aliases, misc)) for t in n.els]
        return env

    def visitList(self, n, vty, aliases, misc):
        if isinstance(n.ctx, ast.Store):
            return self.visitTuple(n, vty, aliases, misc)
        else: return {}

    def visitWith(self, n, vty, aliases, misc):
        if flags.PY_VERSION == 3 and flags.PY3_VERSION >= 3:
            env = {}
            for item in n.items:
                update(self.dispatch(item, True, aliases, misc), env, location=n, file=self.filename)
        else:
            env = self.dispatch(n.optional_vars, True, aliases, misc) if n.optional_vars else {}
        with_env = self.dispatch(n.body, vty, aliases, misc)
        update(with_env, env, location=n, file=self.filename)
        return env

    def visitwithitem(self, n, vty, aliases, misc):
        return self.dispatch(n.optional_vars, vty, aliases, misc) if n.optional_vars else {}

    def visitExceptHandler(self, n, vty, aliases, misc):
        if n.name:
            if flags.PY_VERSION == 3:
                env = {Var(n.name, n): Dyn}
            elif flags.PY_VERSION == 2:
                env = self.dispatch(n.name, True, aliases, misc)
        else:
            env = {}
        b_env = self.dispatch(n.body, vty, aliases, misc)
        update(b_env, env, location=n, file=self.filename)
        return env
