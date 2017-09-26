from . import ctypes, cgen_helpers, constraints
from .. import typing, visitors, exc, argspec, retic_ast, env
import ast
from collections import namedtuple

tydict = typing.Dict[str, ctypes.CType]

def argvar(arg, name, kind):
    if hasattr(arg, 'retic_ctype'):
        return arg.retic_ctype
    else:
        ty = arg.retic_ctype = ctypes.CVar(name='<{}>{}<{}>'.format(name, kind, arg.arg))
        return ty

def setup_arg_types(n, name):
    args = {}
    for arg in n.args:
        args[arg.arg] = argvar(arg, name, 'arg')
    for arg in n.kwonlyargs:
        args[arg.arg] = argvar(arg, name, 'kwoarg')
    if n.vararg:
        args[n.vararg.arg] = ctypes.CHTuple(argvar(n.vararg, name, 'vararg'))
    if n.kwarg:
        args[n.kwarg.arg] = ctypes.CDict(ctypes.CStr(), argvar(n.kwarg, name, 'kwarg'))
    return args



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
        iter, stp = cgen_helpers.iterable_type(comp.iter.retic_ctype)
        st |= stp
        assigns, stp = decomp_assign(comp.target, iter)
        st |= stp
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
        return {lhs: rhs}, set()
    elif isinstance(lhs, ast.Tuple) or isinstance(lhs, ast.List):
        if isinstance(rhs, ctypes.CDyn):
            st = set()
            dct = {}
            for lhe in lhs.elts:
                d, stp = decomp_assign(lhe, ctypes.CDyn(), level_up=rhs)
                st |= stp
                dct.update(d)
            return dct, stp
        elif isinstance(rhs, ctypes.CList) or isinstance(rhs, ctypes.CHTuple):
            st = set()
            dct = {}
            for lhe in lhs.elts:
                d, stp = decomp_assign(lhe, rhs.elts, level_up=rhs)
                st |= stp
                dct.update(d)
            return dct, stp
        elif isinstance(rhs, ctypes.CTuple):
            if len(lhs.elts) == len(rhs.elts):
                st = set()
                dct = {}
                for lhe, rhe in zip(lhs.elts, rhs.elts):
                    d, stp = decomp_assign(lhe, rhe, level_up=rhs)
                    st |= stp
                    dct.update(d)
                return dct, stp
            else: raise exc.InternalReticulatedError(lhs)
        elif isinstance(rhs, ctypes.CVar):
            dct = {}
            st = set()
            elts = []
            for i, lhe in enumerate(lhs.elts):
                var = ctypes.CVar(rhs.rootname + '%assign{}'.format(i))
                elts.append(var)
                d, stp = decomp_assign(lhe, var, level_up=rhs)
                st |= stp
                for k, v in d.items():
                    dct[k] = v
            return dct, (stp | {constraints.CheckC(rhs, retic_ast.Tuple(*([retic_ast.Dyn()] * len(lhs.elts))), ctypes.CTuple(*elts))})
        else: raise exc.InternalReticulatedError(lhs, rhs)
    elif isinstance(lhs, ast.Starred):
        return decomp_assign(lhs.value, CList(elts=rhs), level_up=level_up)
    else: 
        raise exc.InternalReticulatedError(lhs, isinstance(lhs, ast.Tuple))



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

class ScopeFinder(visitors.SetGatheringVisitor):
    def visitModule(self, n, topenv, *args):
        env, st = getModuleScope(n, topenv)
        n.retic_cenv = env
        return st | self.dispatch(n.body, env)

    def visitFunctionDef(self, n, env, *args):
        # getFunctionScope will update the ast.arg's of the function with .retic_types.
        # do this before dispatching on n.args so that visitarguments can check default types
        fun_env, st = getFunctionScope(n, env)

        st |= self.dispatch(n.args, env, *args)
        from . import constrgen
        st |= constrgen.U([self.dispatch(dec, env, *args) for dec in n.decorator_list])

        # Attaching return type
        if not hasattr(n, 'retic_return_ctype'):
            n.retic_return_ctype = ctypes.CVar('<{}>return'.format(n.name))
        n.retic_cenv = fun_env

        return st | self.dispatch(n.body, fun_env, *args)

    def visitClassDef(self, n, env, *args):
        # When we recur into the ClassDef, functions and lambdas have
        # the scope of the rest of the world outside of the
        # classdef. Nested classdefs actually do too! 
        scope = env.copy()
        scope.update(n.retic_member_cenv)
        n.retic_cenv = scope
        return self.dispatch(n.body, env, *args)


def local_types(ext_scope, ext_fixed, body):
    from .. import scope
    # Find assignment targets
    assgn_targets = scope.WriteTargetFinder().preorder(body)
    scope = {k: ctypes.CVar(name=k) for k in assgn_targets if k not in ext_fixed}
    ret_scope = ext_scope.copy()
    ret_scope.update(scope)
    return ret_scope



def getModuleScope(n: ast.Module, surrounding:tydict):
    theclasses, classenv, ctbl, st = get_class_scope(n.body, surrounding, n.retic_import_cenv)
    n.retic_cctbl = ctbl

    local = InitialScopeFinder().preorder(n.body, False)
    local.update(classenv)
    local.update(n.retic_import_cenv)
    modscope = surrounding.copy() if surrounding else {}
    modscope.update(env.module_cenv())
    modscope.update(local)
    local = local_types(modscope, local, n.body)
    return local, st


# Determines the internal scope of a function and updates the arguments with .retic_type
def getFunctionScope(n: ast.FunctionDef, surrounding: tydict)->tydict:
    theclasses, classenv, _, st = get_class_scope(n.body, surrounding, n.retic_import_cenv)
    local = InitialScopeFinder().preorder(n.body, False)
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
    return ret, st

class InitialScopeFinder(visitors.DictGatheringVisitor):
    examine_functions = False

    def combine_stmt(self, s1, s2):
        s1.update(s2)
        return s1
    
    def visitClassDef(self, n, *args):
        return {}

    def visitFunctionDef(self, n: ast.FunctionDef, ismethod, *args):
        n.retic_ismethod = ismethod
        # argbindings = []
        # for arg in n.args.args:
        #     argty = argvar(arg, n.name, 'arg')
        #     argbindings.append((arg.arg, argty))

        # if n.args.vararg or n.args.kwonlyargs or n.args.kwarg or n.args.defaults:
        #     if n.args.defaults:
        #         argbindings = argbindings[:-len(n.args.defaults)]
        #     argsty = ctypes.ArbCAT()
        # else:
        #     argsty = ctypes.PosCAT([v for k, v in argbindings])

        sig = argspec.csignature(n.args, argvar, n.name)
        argsty = ctypes.SpecCAT(sig)

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
                        if n.args.vararg or n.args.kwonlyargs or n.args.kwarg or n.args.defaults:
                            raise Exception()
                        funty.froms = ctypes.PosCAT([argsty.spec.parameters[p].annotation for p in argsty.spec.parameters])
                elif isinstance(dec, ast.Attribute):
                    if isinstance(dec.value, ast.Name) and dec.attr in ['setter', 'getter', 'deleter']:
                        return {}

        return {n.name: funty}


class_with_type = namedtuple('class_with_type', ['theclass', 'type'])




def generate_mro(n, ctbl):
    goto_dyn = False
    classmap = {'CDyn': type('CDyn', (), {})}
    rev_classmap = {classmap['CDyn']: DynClassTblEntry()}
    def build_classmap(cls):
        nonlocal goto_dyn
        if isinstance(cls, ClassTblEntry):
            if cls in classmap:
                return classmap[cls]
            inhs = []
            for inh in cls.inherits:
                inh = ctbl[inh]
                bcm = build_classmap(inh)
                if bcm is not None and bcm not in inhs:
                    inhs.append(bcm)
            cty = type(cls.name, tuple(inhs), {})
            classmap[cls] = cty
            rev_classmap[cty] = cls
            return cty
        else:
            assert isinstance(cls, DynClassTblEntry)
            goto_dyn = True
            return None
    
    ty = build_classmap(ctbl[n.name])
    mro = ty.mro()
    return [rev_classmap[c] for c in mro[:-1]] + ([DynClassTblEntry()] if goto_dyn else [base()])

class DynClassTblEntry:
    def instance_supports(self, k, ctbl):
        return True
        
    def instance_lookup(self, k, ctbl):
        return ctypes.CDyn()

    def supports(self, k, ctbl):
        return True

    def lookup(self, k, ctbl):
        return ctypes.CDyn()

class ClassTblEntry:
    def __init__(self, name, members, fields):
        self.tyvar = ctypes.CTyVar(name)
        self.name = name
        self.members = members
        self.fields = fields
        self.inherits = []
        self.dynamized = False
        
    def __str__(self):
        return '{} class {} extends {}:\nMEMBERS: {}\nFIELDS: {}'.format(('dynamic' if self.dynamized else ''), self.name, self.inherits, self.members, self.fields)

    def __repr__(self):
        return str(self)
    def __hash__(self):
        return id(self)
    def __eq__(self, other):
        return other is self

    def superclasses(self, ctbl):
        return [self.name] + sum([ctbl[sup].superclasses(ctbl) for sup in self.inherits], [])

    def subst(self, x, t):
        t = t.subst(ctypes.CInstance(self.name), self.tyvar)
#        if isinstance(t, ctypes.CInstance) and t.instanceof == self.name:
#            t = self.tyvar
        self.members = {mem: self.members[mem].subst(x, t) for mem in self.members}
        self.fields = {fld: self.fields[fld].subst(x, t) for fld in self.fields}

    def vars(self, ctbl):
        return sum([self.members[mem].vars(ctbl) for mem in self.members], []) + sum([self.fields[fld].vars(ctbl) for fld in self.fields], []) + \
            sum([ctbl[sup].vars(ctbl) for sup in self.inherits], [])

    def types(self, ctbl):
        return list(self.members.values()) + list(self.fields.values()) + sum([ctbl[sup].types(ctbl) for sup in self.inherits], [])

    def get_mro(self, ctbl):        
        if hasattr(self, 'mro'):
            return self.mro
        else:
            self.mro = generate_mro(self, ctbl)
            return self.mro

    def instance_supports(self, k, ctbl):
        try:
            self.instance_lookup(k, ctbl)
            return True
        except KeyError:
            return False
        
    def instance_lookup(self, k, ctbl):
        mro = self.get_mro(ctbl)
        for cls in mro:
            try:
                return cls.fields[k].subst(cls.tyvar, ctypes.CInstance(cls.name))
            except KeyError:
                try:
                    return cls.members[k].bind().subst(cls.tyvar, ctypes.CInstance(cls.name))
                except KeyError:
                    pass
        raise KeyError()

    def supports(self, k, ctbl):
        try:
            self.lookup(k, ctbl)
            return True
        except KeyError:
            return False

    def lookup(self, k, ctbl, loop=False):
        if not loop and k == '__init__':
            init = self.lookup(k, ctbl, loop=True)
            if isinstance(init, ctypes.CFunction):
                return ctypes.CFunction(init.froms, ctypes.CInstance(self.name))
            else: 
                return init

        mro = self.get_mro(ctbl)

        for cls in mro:
            try:
                return cls.members[k].subst(cls.tyvar, ctypes.CInstance(cls.name))
            except KeyError:
                pass
        raise KeyError()

def base():
    return ClassTblEntry('$base', {'__init__':ctypes.CFunction(ctypes.ArbCAT(), ctypes.CDyn())}, {})

def get_class_scope(stmts, surrounding, import_env):
    from .. import scope as _scp
    from .. import pragmas
    classes = ClassFinder().preorder(stmts)
    classenv = { name: classes[name].type for name in classes }
    ctbl = {'object': ClassTblEntry('object', {}, {})}
    st = set()

    for name in classes:
        cwt = classes[name]
        classscope = surrounding.copy() if surrounding else {} 

        # Need to get definitions for subclasses too
        subclasses, subclassenv, sctbl, stp = get_class_scope(cwt.theclass.body, surrounding, import_env)
        st |= stp

        classdefs = InitialScopeFinder().preorder(cwt.theclass.body, ctypes.CInstance(cwt.type.name))
        if '__init__' in classdefs and isinstance(classdefs['__init__'], ctypes.CFunction):
            st |= {constraints.STC(ctypes.CInstance(name), classdefs['__init__'].to)}
        classvars = {name: ctypes.CVar(name=name) for name in classdefs}
        st |= {constraints.STC(classdefs[name], classvars[name]) for name in classdefs}
        classscope.update(classvars)
        #classscope.update(classdefs)
        classscope.update(subclassenv)

        cwt.theclass.retic_csubclasses = subclasses.values()

        classscope.update(import_env) 
        
        members = _scp.WriteTargetFinder().preorder(cwt.theclass.body)
        classscope.update({n: ctypes.CVar(name=n) for n in members})

        classscope.update({n: ctypes.CVar(name=n) for n in cwt.theclass.retic_annot_members})

        tymems = classscope
        tyfields = {n: ctypes.CVar(name=n) for n in cwt.theclass.retic_annot_fields}

        cwt.theclass.retic_ctype = ctypes.CClass(name)
        ctbl.update(sctbl)
        ctbl[name] = ClassTblEntry(cwt.theclass.name, tymems, tyfields)

        #cwt.theclass.retic_ctype = ctypes.CClass(name, tymems, tyfields)
        cwt.theclass.retic_member_cenv = classscope

    return classes, classenv, ctbl, st

class ClassFinder(visitors.DictGatheringVisitor):
    examine_functions = True

    def visitClassDef(self, n, *args):
        return { n.name: class_with_type(theclass=n, type=ctypes.CClass(n.name)) }

