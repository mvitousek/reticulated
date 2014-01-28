import ast, typing, flags
from vis import Visitor
from visitors import DictGatheringVisitor, GatheringVisitor
from typing import *
from relations import *
from exc import StaticTypeError

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

class ObjectAlias(typing.PyType):
    def __init__(self, name):
        self.name = name
    def __str__(self):
        return 'OBJECTALIAS(%s)' % self.name
    def __eq__(self, other):
        return isinstance(other, ObjectAlias) and other.name == self.name
    def substitute(self, var, ty):
        if self.name == var:
            return ty
        else: return self
    def copy(self):
        return ObjectAlias(self.name)
class Object(typing.PyType):
    def __init__(self, name, members):
        self.name = name
        self.members = members.copy()
    def __str__(self):
        return 'Obj(%s)%s' % (self.name, str(self.members))
    def __eq__(self, other):
        return isinstance(other, Object) and other.name == self.name and \
            other.members == self.members
    def substitute(self, var, ty):
        ty = ty.copy()
        ty = ty.substitute(self.name, TypeVariable(self.name))
        self.members = {k:self.members[k].substitute(var, ty) for k in self.members}
        return self
    def copy(self):
        return Object(self.name, {k:self.members[k].copy() for k in self.members})

class Classfinder(DictGatheringVisitor):
    examine_functions = False
    def combine_stmt(self, scope1, scope2):
        for x in scope2:
            if x in scope1:
                scope1[x] = typing.Dyn
            else: scope1[x] = scope2[x]
        return scope1
    def combine_expr(self, scope1, scope2):
        return {}
    def combine_stmt_expr(self, stmt, expr):
        return stmt

    def visitClassDef(self, n):
        return { n.name : ObjectAlias(n.name) }

class Typefinder(GatheringVisitor):
    examine_functions = False
    empty_stmt = lambda self: ({}, set(), {})
    empty_expr = lambda self: set()

    classfinder = Classfinder()

    def __init__(self, type_inference):
        super(Typefinder, self).__init__()
        self.vartype = typing.Bottom if type_inference else typing.Dyn

    def dispatch_scope(self, n, env, constants, tyenv=None):
        if tyenv == None:
            tyenv = {}
        if not hasattr(self, 'visitor'): # preorder may not have been called
            self.visitor = self
        defs = {}
        externals = set([])
        class_aliases = self.classfinder.dispatch_statements(n)
        class_aliases.update(tyenv)
        print(class_aliases)
        alias_map = {}
        for s in n:
            add, kill, fixed_aliases = self.dispatch(s, class_aliases)
            externals.update(kill)
            update(add, defs, constants)
            alias_map.update(fixed_aliases)
            
        while True:
            new_map = alias_map.copy()
            print('MAP', alias_map)
            for alias1 in new_map:
                for alias2 in alias_map:
                    if alias1 == alias2:
                        continue
                    else:
                        new_map[alias1] = new_map[alias1].copy().substitute(alias2, alias_map[alias2].copy())
            if new_map == alias_map:
                break
            else: alias_map = new_map
        # De-alias
        for var in defs:
            for alias in new_map:
                defs[var] = defs[var].substitute(alias, new_map[alias])
        print('MAP', new_map)
        for k in externals:
            if k in defs:
                if x in env and normalize(defs[x]) != normalize(env[x]):
                    raise StaticTypeError('Global assignment of incorrect type')
                else:
                    del defs[x]
                    del indefs[x]
        print('DEFS', defs)
        indefs = constants.copy()
        indefs.update(defs)
        return indefs, defs
            
    def combine_expr(self, s1, s2):
        s2.update(s1)
        return s1

    def combine_stmt(self, s1, s2):
        s1env, s1kill, s1alias = s1
        s2env, s2kill, s2alias = s2
        update(s1env, s2env)
        s2kill.update(s1kill)
        s2alias.update(s1alias)
        return s2env, s2kill, s2alias

    def combine_stmt_expr(self, stmt, expr):
        senv, skill, salias = stmt
        update(senv, expr)
        return expr, skill, salias
    
    def default_expr(self, n):
        return {}
    def default_stmt(self, n):
        return {}, set(), {}

    def visitAssign(self, n, aliases):
        vty = self.vartype
        env = {}
        for t in n.targets:
            env.update(self.dispatch(t, vty))
        return env, set(), {}

    def visitFor(self, n, aliases):
        vty = self.vartype
        env = self.dispatch(n.target, vty)
        for_env, for_kill, for_alias = self.dispatch_statements(n.body, aliases)
        else_env, else_kill, else_alias = self.dispatch_statements(n.orelse, aliases)
        update(for_env, env)
        update(else_env, env)
        for_kill.update(else_kill)
        for_alias,update(else_alias)
        return (env, for_kill, for_alias)

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
                return ({n.name: annoty}, set([]), {})
            else: raise StaticTypeError('Annotated type does not match type of function (%s </~ %s)' % (ty, annoty))
        else:
            return ({n.name: ty}, set([]), {})

    def visitClassDef(self, n, aliases):
        def_finder = Typefinder(type_inference=False)
        internal_aliases = aliases.copy()
        internal_aliases.update({n.name:TypeVariable(n.name), 'Self':Self()})
        _, defs = def_finder.dispatch_scope(n.body, {}, {}, internal_aliases)
        print(n.name, 'has type', defs)
        return {n.name: Bottom}, set([]), {n.name:Object(n.name, defs)}
        
    def visitName(self, n, vty):
        if isinstance(n.ctx, ast.Store):
            return {n.id: vty}
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
        (with_env, kill, alias) = self.dispatch_statements(n.body, aliases)
        update(with_env, env)
        return (env, kill, alias)

    def visitExceptHandler(self, n, aliases):
        vty = Dyn
        if n.name:
            if flags.PY_VERSION == 3:
                env = {n.name: vty}
            elif flags.PY_VERSION == 2:
                env = self.dispatch(n.name, Dyn)
        else:
            env = {}
        (b_env, kill, alias) = self.dispatch_statements(n.body, aliases)
        update(b_env, env)
        return (env, kill, alias)

    def visitGlobal(self, n, aliases):
        return ({}, set(n.names), {})

    def visitNonlocal(self, n, aliases):
        return ({}, set(n.names), {})

