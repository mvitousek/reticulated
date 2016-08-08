from . import visitors, exc, retic_ast, imports, scope, pragmas
from collections import namedtuple
import ast

class_with_type = namedtuple('class_with_type', ['theclass', 'type'])


def get_class_scope(n, surrounding, aliases):
    DuplicateClassFinder().preorder(n)
    classes = ClassFinder().preorder(n)
    classenv = { name: classes[name].type for name in classes }
    typeenv = { name: retic_ast.Instance(classenv[name]) for name in classenv }

    aliases = aliases.copy()
    aliases.update(typeenv)

    for name in classes:
        cwt = classes[name]

        classscope = surrounding.copy() if surrounding else {} 
        classdefs = scope.InitialScopeFinder().preorder(cwt.theclass.body, aliases)
        classscope.update(classdefs)
        classscope.update(n.retic_import_env) 
        
        members = scope.WriteTargetFinder().preorder(cwt.theclass.body)
        classscope.update({n: retic_ast.Dyn() for n in members})

        pragmas.ClassAnnotationHandler().preorder(cwt.theclass, aliases)

        cwt.theclass.retic_uncertain_members = { k: cwt.theclass.retic_annot_members[k] for k in cwt.theclass.retic_annot_members if k not in classscope }

        classscope.update(cwt.theclass.retic_annot_members)

        cwt.type.members.update(classscope)
        cwt.type.fields.update(cwt.theclass.retic_annot_fields)

        cwt.theclass.retic_member_env = classscope

    return classes, classenv, typeenv

def try_to_finalize_class(cwt:class_with_type, scope):
    n, ty = cwt.theclass, cwt.type
    from . import typecheck
    
    if cwt.type.initialized:
        # Class never gets unfinalized
        return True
    
    scope = scope.copy()
    scope.update(n.retic_member_env)

    [typecheck.Typechecker().preorder(base, scope, {}) for base in n.bases]

    types = [base.retic_type for base in n.bases]
    if all((isinstance(inht, retic_ast.Class) and inht.initialized) or isinstance(inht, retic_ast.Dyn) for inht in cwt.type.inherits):
        cwt.type.inherits.extend(types)
        cwt.type.initialized = True
        cwt.theclass.retic_env = scope
        cwt.theclass.retic_type = cwt.type
        # Now that the class is finalized and we can see all the
        # members it should have, make sure that it supports all the
        # members it claims to.
        check_members(cwt.theclass)
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

class DuplicateClassFinder(visitors.SetGatheringVisitor):
    def combine_stmt(self, n1, n2):
        inter = n1.intersection(n2)
        if inter:
            raise exc.StaticTypeError(None, 'Duplicate definitions of class {} in scope'.format(list(inter)[0]))
        return n1.union(n2)

    def visitClassDef(self, n):
        return {n.name}

class ClassFinder(visitors.DictGatheringVisitor):
    def visitClassDef(self, n, *args):
        return { n.name: class_with_type(theclass=n, type=retic_ast.Class(n.name)) }
