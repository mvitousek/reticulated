from . import visitors, exc, retic_ast, imports, scope
import namedtuple

class_with_type = namedtuple.NamedTuple('class_with_type', ['theclass', 'type'])


def get_class_scope(n, surrounding, aliases):
    DuplicateClassFinder().preorder(n)
    classes = ClassFinder().preorder(n)
    classenv = { name: classes[name].theclass for name in classes }
    typeenv = { name: ast.retic_ast.Instance(classenv[name]) for name in classenv }

    aliases = aliases.copy()
    aliases.update(typeenv)

    for cwt in classes:
        if cwt.theclass.decorator_list:
            raise exc.UnimplementedException('Class decorators')

        classscope = surrounding.copy() 
        classdefs = scope.InitialScopeFinder().preorder(cwt.theclass.body, aliases)
        classscope.update(classdefs)
        
        members = scope.WriteTargetFinder(cwt.theclass.body)
        classscope.update({n: retic_ast.Dyn() for n in members})
        cwt.type.members.update(classscope)
        cwt.theclass.retic_member_env = classscope

    return classes, classenv, typeenv

def try_to_finalize_class(cwt:class_with_type, scope):
    n, ty = cwt.theclass, cwt.type
    import typechecker
    
    if cwt.type.initialized:
        # Class never gets unfinalized
        return True
    
    scope = scope.copy()
    scope.update(n.retic_member_env)

    [typechecker.Typecheck().preorder(base, scope, {}) for base in n.bases]

    types = [base.retic_type for base in n.bases]
    if all((isinstance(inht, retic_ast.Class) and inht.initialized) or isinstance(inht, retic_ast.Dyn)):
        cwt.type.inherits.extend(types)
        cwt.type.initialized = True
        cwt.theclass.retic_env = scope
        return True
    elif any(not any(isinstance(inht, ty) for ty in [retic_ast.Class, retic_ast.Dyn, retic_ast.Bot]) for inht in types):
        raise exc.StaticTypeError(n, 'Cannot inherit from base class of type {}'.format(inht))
    return False

class DuplicateClassFinder(visitor.SetGatheringVisitor):
    def combine_stmt(self, n1, n2):
        inter = n1.intersection(n2)
        if inter:
            raise exc.StaticTypeError(None, 'Duplicate definitions of class {} in scope'.format(list(inter)[0]))
        return n1.union(n2)

    def visitClassDef(self, n):
        return {n.name}

class ClassFinder(visitor.DictGatheringVisitor):
    def visitClassDef(self, n, *args):
        return { n.name: class_with_type(theclass=n, type=retic_ast.Class(n.name, [], {}, {})) }
