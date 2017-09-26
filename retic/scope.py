from . import visitors, retic_ast, typing, typeparser, exc, consistency, env, argspec
import ast

## This module figures out the environment for a given scope. 

tydict = typing.Dict[str, retic_ast.Type]

class InconsistentAssignment(Exception): pass


# Determines the internal scope of a comprehension, and dispatches the
# typechecker on the comprehensions.  used directly from the typechecker.
def getComprehensionScope(n: typing.List[ast.comprehension], env: tydict, 
                          typechecker: 'Typechecker', *args)->tydict:
    # We pass in the typechecker because later comprehensions are in
    # the scope of the earlier comprehensions
    env = env.copy()
    for comp in n:
        # The iter of the comp is not in the scope of the target
        typechecker.dispatch(comp.iter, env, *args)
        # Get the types of the bound variables from the assignment. Do
        # not dispatch on the target yet because it isn't in
        # scope. Recall that comprehensionvars (in 3.0+) are in a
        # separate scope from the rest of the world
        try:
            assigns = decomp_assign(comp.target, consistency.iterable_type(comp.iter.retic_type))
        except consistency.BadTypeOp:
            raise exc.StaticTypeError(comp.iter, 'Cannot iterate over value of type {}'.format(comp.iter.retic_type))
        env.update({k.id: assigns[k] for k in assigns if isinstance(k, ast.Name)})
        
        typechecker.dispatch(comp.ifs, env, *args)
        typechecker.dispatch(comp.target, env, *args)
        comp.retic_type = comp.target.retic_type
    return env


# Determines the internal scope of a lambda. used directly from the typechecker.
def getLambdaScope(n: ast.Lambda, surrounding: tydict)->tydict:
    args = getLocalArgTypes(n.args, {}) # Lambdas currently can't have annotations, so we can pass in an empty aliases list
    scope = surrounding.copy()
    scope.update(args)
    return scope


# Given a writable (LHS) AST node and a type, figure out which types
# correspond to indvidual non-destructurable targets in the AST node.
def decomp_assign(lhs: ast.expr, rhs: retic_ast.Type, level_up=None):
    
    if isinstance(lhs, ast.Name) or isinstance(lhs, ast.Subscript) or isinstance(lhs, ast.Attribute):
        return {lhs: rhs}
    if isinstance(lhs, ast.Tuple) or isinstance(lhs, ast.List):
        if isinstance(rhs, retic_ast.Dyn):
            return {k: v for d in [decomp_assign(lhe, retic_ast.Dyn(), level_up=rhs) for lhe in lhs.elts] for k, v in d.items()}
        elif isinstance(rhs, retic_ast.Bot):
            return {k: v for d in [decomp_assign(lhe, retic_ast.Bot(), level_up=rhs) for lhe in lhs.elts] for k, v in d.items()}
        elif isinstance(rhs, retic_ast.List) or isinstance(rhs, retic_ast.HTuple):
            return {k: v for d in [decomp_assign(lhe, rhs.elts, level_up=rhs) for lhe in lhs.elts] for k, v in d.items()}
        elif isinstance(rhs, retic_ast.Tuple):
            if len(lhs.elts) == len(rhs.elts):
                return {k: v for d in [decomp_assign(lhe, rhe, level_up=rhs) for lhe, rhe in zip(lhs.elts, rhs.elts)] for k, v in d.items()}
            else: raise exc.StaticTypeError(lhs, 'Value of type {} cannot be destructured for assignment to target'.format(rhs, typeparser.unparse(lhs)))
        else: raise exc.StaticTypeError(lhs, 'Value of type {} cannot be destructured for assignment'.format(rhs))
    elif isinstance(lhs, ast.Starred):
        return decomp_assign(lhs.value, retic_ast.List(elts=rhs), level_up=level_up)
    else: 
        raise exc.InternalReticulatedError(lhs)
        

# Performs local type inference on a scope. ext_scope is the overall
# scope this takes place in (some of which may be shadowed by locals),
# while ext_fixed are the annotated variables in the same scope which
# cannot be shadowed.
def infer_types(ext_scope: tydict, ext_fixed: tydict, body: typing.List[ast.stmt], classdefs)->tydict:
    from . import classes
    # Find assignment targets
    infer_targets = WriteTargetFinder().preorder(body)
    # Create a scope for the locals that aren't already defined by a
    # type annotation. Initialize everything to the bottom type
    bot_scope = {k: retic_ast.Bot() for k in infer_targets if k not in ext_fixed}

    from .typecheck import Typechecker

    classes_finalized = False

    while True:
        old_bot_scope = bot_scope.copy()
        # Add the inference scope to the overall scope. We don't
        # shadow fixed things since we kept them out of bot_scope
        # above
        infer_scope = ext_scope.copy()
        infer_scope.update(bot_scope)

        # Find all bindings in the current body
        assignments = AssignmentFinder().preorder(body)

        # Typecheck the body, skipping any static type errors.
        # Originally, for each binding, we typecheck the RHS of every
        # assignment in the infer_scope. However, once the type
        # environment can vary based on if statements etc, we can't
        # rely on this, because the proper scope for an assignment can
        # be more precise than the initial environment for this
        # scope. Instead, we typecheck the whole body using a subtype
        # of the usual typechecker that just ignores function- and
        # classdefs (since they have their own scopes, which are not
        # yet known)
        try:
            local_scope_typechecker().preorder(body, infer_scope, {})
        except exc.StaticTypeError:
            # Static type errors should result in remaining variables
            # being treated as Bot, because we might be doing an
            # operation on a value that is still going "up the
            # ladder". I think we don't need to worry about Bots still
            # existing after reaching a fixpoint, because these terms
            # will be re-typechecked when we do the main whole-module
            # typechecking pass. Since we're typecheckin the whole
            # body here, we will have to set the retic_type for each
            # val without a retic_type to Dyn() when we iterate over
            # the arguments -- see below
            pass

        for targ, val, kind in assignments:
            # In case of static type error -- see above
            if not hasattr(val, 'retic_type'):
                val.retic_type = retic_ast.Bot()

            # Then decompose the assignment to the level of individual
            # variables. Join the current type for the variable to the
            # type of the RHS and write that back into bot_scope.
            if kind == 'ASSIGN':
                assigns = decomp_assign(targ, val.retic_type)
                for targ in assigns:
                    if isinstance(targ, ast.Name) and targ.id in bot_scope:
                        #print('join', targ.id, assigns[targ], bot_scope[targ.id], '=', consistency.join(assigns[targ], bot_scope[targ.id]))
                        #bot_scope[targ.id] = consistency.join(solveflows.make_variable(assigns[targ]), bot_scope[targ.id])
                        bot_scope[targ.id] = consistency.join(assigns[targ], bot_scope[targ.id])
            elif kind == 'FOR':
                try:
                    iter = consistency.iterable_type(val.retic_type)
                except consistency.BadTypeOp:
                    iter = retic_ast.Bot()
                assigns = decomp_assign(targ, iter)
                for targ in assigns:
                    if isinstance(targ, ast.Name) and targ.id in bot_scope:
                        #bot_scope[targ.id] = consistency.join(solveflows.make_variable(assigns[targ]), bot_scope[targ.id])
                        bot_scope[targ.id] = consistency.join(assigns[targ], bot_scope[targ.id])
            elif kind == 'INSTANCE':
                # In this branch, the targ is a STRING, not an ast node
                try:
                    inst = consistency.instance_type(val.retic_type)
                except consistency.BadTypeOp:
                    inst = retic_ast.Bot()
                if targ in bot_scope:
                    #bot_scope[targ] = consistency.join(solveflows.make_variable(inst), bot_scope[targ])
                    bot_scope[targ] = consistency.join(inst, bot_scope[targ])
            else:
                raise exc.InternalReticulatedError(kind)
        
            
        # If bot_scope is free of Bots and all classes are
        # initialized, and we've already had one iteration with all
        # classes finalized, then we're done. Otherwise do another
        # iteration.
        if bot_scope == old_bot_scope and classes_finalized:
            break
            
        if not classes_finalized:
            classes_finalized = all([classes.try_to_finalize_class(classdefs[cwt], infer_scope) for cwt in classdefs])

    ret = ext_scope.copy()
    ret.update(bot_scope)
    return ret
    

# Determines the internal scope of a function and updates the arguments with .retic_type
def getFunctionScope(n: ast.FunctionDef, surrounding: tydict, aliases)->tydict:
    from . import classes
    try:
        aliases = gather_aliases(n, aliases)
        aliases.update(n.retic_import_aliases.copy())
        theclasses, classenv, aliasenv = classes.get_class_scope(n.body, surrounding, n.retic_import_env, aliases)
        local = InitialScopeFinder().preorder(n.body, aliases)
        local.update(classenv)
        local.update({k: surrounding[k] for k in NonLocalFinder().preorder(n.body)})
        local.update(n.retic_import_env) # We probably want to make
                                         # sure there's no conflict
                                         # between imports and
                                         # annotated locals
    except InconsistentAssignment as e:
        raise exc.StaticTypeError(n, 'Multiple bindings of {} occur in the scope of {} with differing types: {} and {}'.format(e.args[0], n.name, e.args[1], e.args[2]))
    args = getLocalArgTypes(n.args, aliases)
    funscope = surrounding.copy()
    
    for k in local:
        if k in args and not consistency.assignable(args[k], local[k]):
            raise exc.StaticTypeError(n, 'Variable {} is bound both as an argument and by a definition in {} with incompatible types: {} and {}'.format(k, n.name, args[k], local[k]))
    local.update(args)
    
    funscope.update(local)
    
    return infer_types(funscope, local, n.body, theclasses), aliases
    

# Determines the internal scope of a top-level module. Returns a
# 3-tuple of the module's environment 
def getModuleScope(n: ast.Module, surrounding:tydict):
    from . import classes
    try:
        aliases = gather_aliases(n, {})
        aliases.update(n.retic_import_aliases.copy())
        theclasses, classenv, aliasenv = classes.get_class_scope(n.body, surrounding, n.retic_import_env, aliases)
        aliases.update(aliasenv)
        local = InitialScopeFinder().preorder(n.body, aliases)
        local.update(classenv)
        local.update(n.retic_import_env) # We probably want to make
                                         # sure there's no conflict
                                         # between imports and
                                         # annotated locals
    except InconsistentAssignment as e:
        raise exc.StaticTypeError(None, 'Multiple bindings of {} occur at the top level with differing types: {} and {}'.format(e.args[0], e.args[1], e.args[2]))
    modscope = surrounding.copy() if surrounding else {}
    modscope.update(env.module_env())
    modscope.update(local)
    inferred = infer_types(modscope, local, n.body, theclasses)
    n.retic_aliases = aliases
    return inferred, aliases

def getLocalArgTypes(n: ast.arguments, aliases)->tydict:
    args = {}
    for arg in n.args:
        ty = typeparser.typeparse(arg.annotation, aliases)
        args[arg.arg] = arg.retic_type = ty
    for arg in n.kwonlyargs:
        ty = typeparser.typeparse(arg.annotation, aliases)
        args[arg.arg] = arg.retic_type = ty
    if n.vararg:
        ty = typeparser.typeparse(n.vararg.annotation, aliases)
        args[n.vararg.arg]  = n.vararg.retic_type = retic_ast.HTuple(ty)
    if n.kwarg:
        ty = typeparser.typeparse(n.kwarg.annotation, aliases)
        args[n.kwarg.arg]  = n.kwarg.retic_type = retic_ast.Dict(retic_ast.Str(), ty)
    return args

class ScopeFinder(visitors.InPlaceVisitor):
    def visitModule(self, n, topenv, *args):
        env, aliases = getModuleScope(n, topenv)
        n.retic_env = env
        self.dispatch(n.body, env, aliases)

    def visitFunctionDef(self, n, env, aliases, *args):
        # getFunctionScope will update the ast.arg's of the function with .retic_types.
        # do this before dispatching on n.args so that visitarguments can check default types
        fun_env, fun_aliases = getFunctionScope(n, env, aliases)

        self.dispatch(n.args, env, aliases, *args)
        [self.dispatch(dec, env, aliases, *args) for dec in n.decorator_list]

        # Attaching return type
        n.retic_return_type = typeparser.typeparse(n.returns, aliases)
        n.retic_env = fun_env

        self.dispatch(n.body, fun_env, fun_aliases, *args)

    def visitClassDef(self, n, *args):
        # When we recur into the ClassDef, functions and lambdas have
        # the scope of the rest of the world outside of the
        # classdef. Nested classdefs actually do too! 
        self.dispatch(n.body, *args)


def gather_aliases(n, env):
    aliases = {}
    while True:
        last_aliases = aliases
        lenv = env.copy()
        lenv.update(last_aliases)
        aliases = TypeAliasFinder().preorder(n.body, lenv)
        if aliases == last_aliases:
            break
    renv = env.copy()
    renv.update(aliases)
    return renv

class TypeAliasFinder(visitors.DictGatheringVisitor):
    def combine_stmt(self, s1: tydict, s2: tydict)->tydict:
        nope = []
        for k in s1:
            if k in s2 and s1[k] != s2[k]:
                nope.append(k)
        for k in nope:
            del s1[k], s2[k]
        s1.update(s2)
        return s1

    def visitClassDef(self, n, *args):
        return dict()

    def visitAssign(self, n, env, *args):
        try:
            ret = {}
            parsed = typeparser.typeparse(n.value, env)
        except exc.MalformedTypeError:
            return {}

        for target in n.targets:
            if isinstance(target, ast.Name):
                if target.id in typeparser.type_names:
                    raise exc.StaticTypeError(n.value, 'Cannot redefine basic types like {}'.format(target.id))
                ret[target.id] = parsed

        return ret

class InitialScopeFinder(visitors.DictGatheringVisitor):
    examine_functions = False

    def combine_stmt(self, s1: tydict, s2: tydict)->tydict:
        for k in s1:
            if k in s2 and s1[k] != s2[k]:
                raise InconsistentAssignment(k, s1[k], s2[k])
        s1.update(s2)
        return s1
    
    def visitClassDef(self, n, *args):
        return {}

    def visitFunctionDef(self, n: ast.FunctionDef, env, *args)->tydict:
        sig = argspec.signature(n.args, env)

        # for arg in n.args.args:
        #     if arg.annotation:
        #         argty = typeparser.typeparse(arg.annotation, env)
        #     else:
        #         argty = retic_ast.Dyn()
        #     argbindings.append((arg.arg, argty))

        # if n.args.vararg or n.args.kwonlyargs or n.args.kwarg or n.args.defaults:
        #     if n.args.defaults:
        #         argbindings = argbindings[:-len(n.args.defaults)]
        #     argsty = retic_ast.ApproxNamedAT(argbindings)
        # else:
        #     argsty = retic_ast.NamedAT(argbindings)

        argsty = retic_ast.SpecAT(sig)
        retty = typeparser.typeparse(n.returns, env)

        funty = retic_ast.Function(argsty, retty)
        n.retic_type = funty

        if n.decorator_list:
            for dec in n.decorator_list:
                if isinstance(dec, ast.Name):
                    if dec.id == 'property':
                        return {n.name: funty.to}
                    elif dec.id == 'positional':
                        if n.args.vararg or n.args.kwonlyargs or n.args.kwarg or n.args.defaults:
                            raise exc.StaticTypeError(n, "Functions with the 'positional' decorator may only have regular function parameters (no defaults, keyword-only args, starargs, or kwargs)")
                        funty.froms = retic_ast.PosAT([argsty.spec.parameters[p].annotation for p in argsty.spec.parameters])
                elif isinstance(dec, ast.Attribute):
                    if isinstance(dec.value, ast.Name) and dec.attr in ['setter', 'getter', 'deleter']:
                        return {}

        return {n.name: funty}

        
class WriteTargetFinder(visitors.SetGatheringVisitor):
    examine_functions = False
    
    def visitClassDef(self, n, *args):
        return { }

    def visitcomprehension(self, n, *args):
        return set()

    def visitName(self, n: ast.Name)->typing.Set[str]:
        if isinstance(n.ctx, ast.Store):
            return { n.id }
        else: return set()

    def visitExceptHandler(self, n: ast.ExceptHandler)->typing.Set[str]:
        sup = super().visitExceptHandler(n)
        if n.name:
            sup.add(n.name)
        return sup

class AssignmentFinder(visitors.SetGatheringVisitor):
    examine_functions = False
    
    def visitClassDef(self, n, *args):
        return { }

    def visitAssign(self, n: ast.Assign):
        return { (targ, n.value, 'ASSIGN') for targ in n.targets if not isinstance(targ, ast.Subscript) and not isinstance(targ, ast.Attribute) }

    def visitAugAssign(self, n: ast.AugAssign):
        if not isinstance(n.target, ast.Subscript) and not isinstance(n.target, ast.Attribute):
            return { (n.target, n.value, 'ASSIGN') }
        else: return set()

    def visitFor(self, n: ast.For): 
        if not isinstance(n.target, ast.Subscript) and not isinstance(n.target, ast.Attribute):
            return set.union({ (n.target, n.iter, 'FOR') }, self.dispatch(n.body), self.dispatch(n.orelse))
        else: return set.union(self.dispatch(n.body), self.dispatch(n.orelse))
        
    def visitwithitem(self, n):
        if n.optional_vars and not isinstance(n.optional_vars, ast.Subscript) and not isinstance(n.optional_vars, ast.Attribute):
            return { (n.optional_vars, n.context_expr, 'ASSIGN') }
        else: return set()

    def visitExceptHandler(self, n):
        sup = super().visitExceptHandler(n)
        if n.name:
            sup.add( (n.name, n.type, 'INSTANCE') )
        return sup
        
class NonLocalFinder(visitors.SetGatheringVisitor):
    def visitNonlocal(self, n):
        return set(n.names)

class GlobalFinder(visitors.SetGatheringVisitor):
    def visitGlobal(self, n):
        return set(n.names)

def local_scope_typechecker():
    from . import typecheck
    # This is the standard typechecker, but it doesn't explore into
    # functions or classes (things with their own scopes)
    class LocalScopeTypechecker(typecheck.Typechecker):
        def visitClassDef(self, n, *args):
            pass
        def visitFunctionDef(self, n, *args):
            pass
    return LocalScopeTypechecker()
