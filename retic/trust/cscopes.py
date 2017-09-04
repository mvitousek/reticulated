from . import ctypes
from ..import typing, visitors
import ast
from collections import namedtuple

tydict = typing.Dict[str, ctypes.CType]

def argvar(arg, name, kind):
    if hasattr(arg, 'retic_ctype'):
        return arg.retic_ctype
    else:
        ty = arg.retic_ctype = ctypes.CVar(name='{}{}<{}>'.format(name, kind, arg.arg))
        return ty

def setup_arg_types(n, name):
    args = {}
    for arg in n.args:
        args[arg.arg] = argvar(arg, name, 'arg')
    for arg in n.kwonlyargs:
        args[arg.arg] = argvar(arg, name, 'kwoarg')
    if n.vararg:
        args[n.vararg.arg] = argvar(n.vararg, name, 'vararg')
    if n.kwarg:
        args[n.kwarg.arg] = argvar(n.kwarg, name, 'kwarg')
    return {k:args[k] for k in args}



# Determines the internal scope of a comprehension, and dispatches the
# typechecker on the comprehensions.  used directly from the typechecker.
def getComprehensionScope(n, env, typechecker, *args)->tydict:
    # We pass in the typechecker because later comprehensions are in
    # the scope of the earlier comprehensions
    env = env.copy()
    st = set()
    for comp in n:
        # The iter of the comp is not in the scope of the target
        st |= typechecker.dispatch(comp.iter, env, *args)
        # Get the types of the bound variables from the assignment. Do
        # not dispatch on the target yet because it isn't in
        # scope. Recall that comprehensionvars (in 3.0+) are in a
        # separate scope from the rest of the world
        assigns = decomp_assign(comp.target, consistency.iterable_type(comp.iter.retic_type))
        env.update({k.id: assigns[k] for k in assigns if isinstance(k, ast.Name)})
        
        st |= typechecker.dispatch(comp.ifs, env, *args)
        st |= typechecker.dispatch(comp.target, env, *args)
        comp.retic_ctype = comp.target.retic_ctype
    return env, st


# Determines the internal scope of a lambda. used directly from the typechecker.
def getLambdaScope(n, surrounding):
    args = setup_arg_types(n.args, 'lambda')
    scope = surrounding.copy()
    scope.update(args)
    return scope



# Given a writable (LHS) AST node and a type, figure out which types
# correspond to indvidual non-destructurable targets in the AST node.
def decomp_assign(lhs, rhs, level_up=None):
    if isinstance(lhs, ast.Name) or isinstance(lhs, ast.Subscript) or isinstance(lhs, ast.Attribute):
        return {lhs: rhs}
    if isinstance(lhs, ast.Tuple) or isinstance(lhs, ast.List):
        if isinstance(rhs, ctypes.CDyn):
            return {k: v for d in [decomp_assign(lhe, ctypes.CDyn(), level_up=rhs) for lhe in lhs.elts] for k, v in d.items()}
        elif isinstance(rhs, ctypes.CList) or isinstance(rhs, ctypes.CHTuple):
            return {k: v for d in [decomp_assign(lhe, rhs.elts, level_up=rhs) for lhe in lhs.elts] for k, v in d.items()}
        elif isinstance(rhs, ctypes.CTuple):
            if len(lhs.elts) == len(rhs.elts):
                return {k: v for d in [decomp_assign(lhe, rhe, level_up=rhs) for lhe, rhe in zip(lhs.elts, rhs.elts)] for k, v in d.items()}
            else: raise exc.InternalReticulatedError(lhs)
        else: raise exc.InternalReticulatedError(lhs)
    elif isinstance(lhs, ast.Starred):
        return decomp_assign(lhs.value, CList(elts=rhs), level_up=level_up)
    else: 
        raise exc.InternalReticulatedError(lhs)



class ImportCollector(visitors.DictGatheringVisitor):
    def visitClassDef(self, n):
        return {}

    def visitImport(self, n):
        env = {}
        for alias in n.names:
            topname = alias.name.split('.')[0]
            if alias.asname:
                env[alias.asname] = ctypes.CVar(name=alias.asname)
            else:
                env[topname] = ctypes.CVar(name=topname)
        return env
                
    def visitImportFrom(self, n):
        label = '.' * n.level + (n.module.split('.')[0] if n.module else '')
        
        env = {}
        for alias in n.names:
            if alias.name == '*':
                raise Exception(n, 'The types of import target {} are not statically known, so Reticulated cannot safely import *'.format(label))

            else:
                # Syntactically know that the name does not have a . in it
                key = alias.asname if alias.asname else alias.name
                env[key] = ctypes.CVar(name=key)
        return env

class ImportProcessor(visitors.InPlaceVisitor):
    examine_functions = True
    
    def visitModule(self, n):
        n.retic_import_cenv = ImportCollector().preorder(n.body)
        return self.dispatch_statements(n.body)

    def visitClassDef(self, n):
        n.retic_import_cenv = ImportCollector().preorder(n.body)

        return self.dispatch_statements(n.body)

    def visitFunctionDef(self, n):
        n.retic_import_cenv = ImportCollector().preorder(n.body)

        if self.examine_functions:
            return self.dispatch_statements(n.body)
        else: return self.empty_stmt()

class ScopeFinder(visitors.InPlaceVisitor):
    def visitModule(self, n, topenv, *args):
        env = getModuleScope(n, topenv)
        n.retic_cenv = env
        self.dispatch(n.body, env)

    def visitFunctionDef(self, n, env, *args):
        # getFunctionScope will update the ast.arg's of the function with .retic_types.
        # do this before dispatching on n.args so that visitarguments can check default types
        fun_env = getFunctionScope(n, env)

        self.dispatch(n.args, env, *args)
        [self.dispatch(dec, env, *args) for dec in n.decorator_list]

        # Attaching return type
        if not hasattr(n, 'retic_return_ctype'):
            n.retic_return_ctype = ctypes.CVar(n.name + 'return')
        n.retic_cenv = fun_env

        self.dispatch(n.body, fun_env, *args)

    def visitClassDef(self, n, env, *args):
        # When we recur into the ClassDef, functions and lambdas have
        # the scope of the rest of the world outside of the
        # classdef. Nested classdefs actually do too! 
        scope = env.copy()
        scope.update(n.retic_member_cenv)
        n.retic_cenv = scope
        self.dispatch(n.body, *args)


def local_types(ext_scope, ext_fixed, body):
    from .. import scope
    # Find assignment targets
    assgn_targets = scope.WriteTargetFinder().preorder(body)
    scope = {k: ctypes.CVar(name=k) for k in assgn_targets if k not in ext_fixed}
    ret_scope = ext_scope.copy()
    ret_scope.update(scope)
    return ret_scope

def module_env():
    from .. import env
    return {n: ctypes.CVar(name=n) for n in env.module_env()}

def getModuleScope(n: ast.Module, surrounding:tydict):
    theclasses, classenv = get_class_scope(n.body, surrounding, n.retic_import_cenv)
    local = InitialScopeFinder().preorder(n.body, surrounding)
    local.update(classenv)
    local.update(n.retic_import_cenv)
    modscope = surrounding.copy() if surrounding else {}
    modscope.update(module_env())
    modscope.update(local)
    local = local_types(modscope, local, n.body)
    return local


# Determines the internal scope of a function and updates the arguments with .retic_type
def getFunctionScope(n: ast.FunctionDef, surrounding: tydict)->tydict:
    theclasses, classenv = get_class_scope(n.body, surrounding, n.retic_import_cenv)
    local = InitialScopeFinder().preorder(n.body)
    local.update(classenv)
    from .. import scope
    local.update({k: surrounding[k] for k in scope.NonLocalFinder().preorder(n.body)})
    local.update(n.retic_import_cenv) # We probably want to make
                                         # sure there's no conflict
                                         # between imports and
                                         # annotated locals
    args = setup_arg_types(n.args, n.name)
    funscope = surrounding.copy()
    
    local.update(args)
    funscope.update(local)
    
    ret = local_types(funscope, local, n.body)
    return ret

class InitialScopeFinder(visitors.DictGatheringVisitor):
    examine_functions = False

    def combine_stmt(self, s1, s2):
        s1.update(s2)
        return s1
    
    def visitClassDef(self, n, *args):
        return {}

    def visitFunctionDef(self, n: ast.FunctionDef, *args):
        argbindings = []
        for arg in n.args.args:
            argty = argvar(arg, n.name, 'arg')
            argbindings.append((arg.arg, argty))

        if n.args.vararg or n.args.kwonlyargs or n.args.kwarg or n.args.defaults:
            if n.args.defaults:
                argbindings = argbindings[:-len(n.args.defaults)]
            argsty = ctypes.ArbCAT()
        else:
            argsty = ctypes.PosCAT([v for k, v in argbindings])

        if hasattr(n, 'retic_return_ctype'):
            retty = n.retic_return_ctype
        else:
            retty = n.retic_return_ctype = ctypes.CVar(n.name + 'return')

        funty = ctypes.CFunction(argsty, retty)
        n.retic_ctype = funty

        if n.decorator_list:
            for dec in n.decorator_list:
                if isinstance(dec, ast.Name):
                    if dec.id == 'property':
                        return {n.name: funty.to}
                    elif dec.id == 'positional':
                        pass
                elif isinstance(dec, ast.Attribute):
                    if isinstance(dec.value, ast.Name) and dec.attr in ['setter', 'getter', 'deleter']:
                        return {}

        return {n.name: funty}


class_with_type = namedtuple('class_with_type', ['theclass', 'type'])

def get_class_scope(stmts, surrounding, import_env):
    from .. import scope as _scp
    from .. import pragmas
    classes = ClassFinder().preorder(stmts)
    classenv = { name: classes[name].type for name in classes }

    for name in classes:
        cwt = classes[name]
        classscope = surrounding.copy() if surrounding else {} 

        # Need to get definitions for subclasses too
        subclasses, subclassenv, subaliasenv = get_class_scope(cwt.theclass.body, surrounding, import_env)

        classdefs = InitialScopeFinder().preorder(cwt.theclass.body, surrounding)
        classscope.update(classdefs)
        classscope.update(subclassenv)

        cwt.theclass.retic_csubclasses = subclasses.values()

        classscope.update(import_env) 
        
        members = _scp.WriteTargetFinder().preorder(cwt.theclass.body)
        classscope.update({n: ctypes.CVar(name=n) for n in members})

        classscope.update({n: ctypes.CVar(name=n) for n in cwt.theclass.retic_annot_members})

        tymems = classscope
        tyfields = {n: ctypes.CVar(name=n) for n in cwt.theclass.retic_annot_fields}

        cwt.theclass.retic_cvar = cwt.type
        cwt.theclass.retic_ctype = ctypes.CClass(name, tymems, tyfields)
        cwt.theclass.retic_member_cenv = classscope

    return classes, classenv

class ClassFinder(visitors.DictGatheringVisitor):
    examine_functions = True

    def visitClassDef(self, n, *args):
        return { n.name: class_with_type(theclass=n, type=ctypes.CVar(name=n.name)) }

