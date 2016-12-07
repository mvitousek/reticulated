from . import visitors, exc, retic_ast, imports, scope, pragmas, consistency
from collections import namedtuple
import ast

class_with_type = namedtuple('class_with_type', ['theclass', 'type'])


def get_class_scope(stmts, surrounding, import_env, aliases):
    DuplicateClassFinder().preorder(stmts)
    classes = ClassFinder().preorder(stmts)
    classenv = { name: classes[name].type for name in classes }
    typeenv = { name: retic_ast.Instance(classenv[name]) for name in classenv }

    aliases = aliases.copy()
    aliases.update(typeenv)


    for name in classes:
        cwt = classes[name]
        classscope = surrounding.copy() if surrounding else {} 

        
        # Need to get definitions for subclasses too
        subclasses, subclassenv, subaliasenv = get_class_scope(cwt.theclass.body, surrounding, import_env, aliases)

        classdefs = scope.InitialScopeFinder().preorder(cwt.theclass.body, aliases)
        classscope.update(classdefs)
        classscope.update(subclassenv)

        cwt.theclass.retic_subclasses = subclasses.values()

        classscope.update(import_env) 
        
        members = scope.WriteTargetFinder().preorder(cwt.theclass.body)
        classscope.update({n: retic_ast.Dyn() for n in members})

        pragmas.ClassAnnotationHandler().preorder(cwt.theclass, aliases)

        cwt.theclass.retic_uncertain_members = { k: cwt.theclass.retic_annot_members[k] for k in cwt.theclass.retic_annot_members if k not in classscope }

        classscope.update(cwt.theclass.retic_annot_members)

        cwt.type.members.update(classscope)
        cwt.type.fields.update(cwt.theclass.retic_annot_fields)

        cwt.theclass.retic_member_env = classscope

    return classes, classenv, typeenv

def get_metaclass(n):
    if n.keywords:
        for kwd in n.keywords:
            if kwd.arg == 'metaclass':
                return kwd.value

    return None

def try_to_finalize_class(cwt:class_with_type, scope):
        
    n, ty = cwt.theclass, cwt.type
    from . import typecheck
    
    if cwt.type.initialized:
        # Class never gets unfinalized
        return True
    

    scope = scope.copy()
    scope.update(n.retic_member_env)

    # Recur on subclasses
    sub_final = all(try_to_finalize_class(sub, scope) for sub in n.retic_subclasses)
    
    [typecheck.Typechecker().preorder(base, scope, {}) for base in n.bases]
    types = [base.retic_type for base in n.bases]

    meta = get_metaclass(n)
    if meta:
        typecheck.Typechecker().preorder(meta, scope, {})
        meta_type = meta.retic_type
        meta_final = (isinstance(meta_type, retic_ast.Class) and meta_type.initialized) or isinstance(meta_type, retic_ast.Dyn)
        if not any(isinstance(meta_type, ty) for ty in [retic_ast.Class, retic_ast.Dyn, retic_ast.Bot]):
            raise exc.StaticTypeError(meta, 'Cannot have a metaclass of type {}'.format(meta_type))
    else: 
        meta_final = True
        meta_type = None

    if meta_final and sub_final and all((isinstance(inht, retic_ast.Class) and inht.initialized) or isinstance(inht, retic_ast.Dyn) for inht in types):
        cwt.type.inherits.extend(types)
        cwt.type.instanceof = meta_type
        cwt.type.initialized = True
        cwt.theclass.retic_env = scope
        cwt.theclass.retic_type = cwt.type
        # Now that the class is finalized and we can see all the
        # members it should have, make sure that it supports all the
        # members it claims to.
        check_members(cwt.theclass)
        check_inherit(cwt.theclass, cwt.type)
        return True
    elif any(not any(isinstance(inht, ty) for ty in [retic_ast.Class, retic_ast.Dyn, retic_ast.Bot]) for inht in types):
        raise exc.StaticTypeError(n, 'Cannot inherit from base class of type {}'.format(inht))
    return False

def check_members(theclass):
    for k in theclass.retic_uncertain_members:
        ourty = theclass.retic_uncertain_members[k]
        for inh in theclass.bases:
            try:
                theirty = inh.retic_type[k]
                if consistency.consistent(ourty, theirty):
                    return
                else:
                    raise exc.StaticTypeError(inh, 'Class is annotated to have a member "{}" with type {}, but in superclass {} "{}" has incompatible type {}'.format(k, ourty, typeparse.unparse(inh), k, theirty))
            except KeyError:
                pass

        if theclass.bases:
            raise exc.StaticTypeError(theclass, 'Class is annotated to have a member "{}" with type {}, but "{}" is neither defined locally nor is it in the type of any of its supertypes'.format(k, ourty, k))
        raise exc.StaticTypeError(theclass, 'Class is annotated to have a member "{}" with type {}, but "{}" is not defined'.format(k, ourty, k))

def check_inherit(theclass, ty):
    def check_against_superclass(sup):
        if isinstance(sup, retic_ast.Dyn):
            return
        assert isinstance(sup, retic_ast.Class)
        for inh in sup.inherits:
            check_against_superclass(inh)
        for mem in ty.members:
            if mem == '__init__': continue
            if mem in sup.members:
                if not consistency.consistent(ty.members[mem], sup.members[mem]):
                    raise exc.StaticTypeError(theclass, 'Supertype {} of class {} expects that member {} have type {}, but {} expects that it have type {}'.format(sup.name, ty.name, mem, sup.members[mem], ty.name, ty.members[mem]))
        for mem in ty.fields:
            if mem in sup.fields:
                if not consistency.consistent(ty.fields[mem], sup.fields[mem]):
                    raise exc.StaticTypeError(theclass, 'Supertype {} of class {} expects that field {} have type {}, but {} expects that it have type {}'.format(sup.name, ty.name, mem, sup.fields[mem], ty.name, ty.fields[mem]))

    for inh in ty.inherits:
        check_against_superclass(inh)
        

class DuplicateClassFinder(visitors.SetGatheringVisitor):
    def combine_stmt(self, n1, n2):
        inter = n1.intersection(n2)
        if inter:
            raise exc.StaticTypeError(None, 'Duplicate definitions of class {} in scope'.format(list(inter)[0]))
        return n1.union(n2)

    def visitClassDef(self, n):
        return {n.name}

class ClassFinder(visitors.DictGatheringVisitor):
    examine_functions = True

    def visitClassDef(self, n, *args):
        return { n.name: class_with_type(theclass=n, type=retic_ast.Class(n.name)) }
