from . import visitors, retic_ast
import ast

# A visitor to look for AST nodes that lack source line information
class LocationFreeFinder(visitors.BooleanOrVisitor):
    examine_functions = True
    def dispatch(self, val, *args):
        if (not hasattr(val, 'lineno') or val.lineno is None) and (isinstance(val, ast.expr) or isinstance(val, ast.stmt)):
            raise Exception(val.__class__, ast.dump(val))
        super().dispatch(val, *args)

# A visitor to look for expression nodes that lack retic_type information
class MissingTypeFinder(visitors.BooleanOrVisitor):
    examine_functions = True
    def dispatch(self, val, *args):
        if isinstance(val, ast.expr) and not hasattr(val, 'retic_type'): 
            raise Exception(val.__class__, ast.dump(val))
        return super().dispatch(val, *args)

# A visitor to look for ill-typed .retic_type nodes
class BadTypeFinder(visitors.BooleanOrVisitor):
    examine_functions = True
    def dispatch(self, val, *args):
        if hasattr(val, 'retic_type') and not isinstance(val.retic_type, retic_ast.Type): 
            raise Exception(val.__class__, ast.dump(val))
        return super().dispatch(val, *args)

# A visitor to find attached retic info on trees that should be naked
class AttachedInfoFinder(visitors.InPlaceVisitor):
    def dispatch(self, n, *args):
        super().dispatch(n, *args)
        if hasattr(n, 'retic_type'):
            raise Exception()
        if hasattr(n, 'retic_ctype'):
            raise Exception()
        if hasattr(n, 'retic_import_aliases'):
            raise Exception()
        if hasattr(n, 'retic_import_env'):
            raise Exception()
        if hasattr(n, 'retic_annot_members'):
            raise Exception()
        if hasattr(n, 'retic_annot_fields'):
            raise Exception()
        if hasattr(n, 'retic_env'):
            raise Exception()
        if hasattr(n, 'retic_cenv'):
            raise Exception()
        if hasattr(n, 'retic_module_type'):
            raise Exception()
        if hasattr(n, 'retic_module_is_package'):
            raise Exception()
        if hasattr(n, 'retic_module_package'):
            raise Exception()
        if hasattr(n, 'retic_aliases'):
            raise Exception()
        if hasattr(n, 'retic_return_type'):
            raise Exception()
        if hasattr(n, 'retic_subclasses'):
            raise Exception()
        if hasattr(n, 'retic_uncertain_members'):
            raise Exception()
        if hasattr(n, 'retic_member_env'):
            raise Exception()
        if hasattr(n, 'retic_import_cenv'):
            raise Exception()

def io(fn):
    import random
    def inner(*args):
        x = random.random()
        print('IN', x, *args)
        r = fn(*args)
        print('OUT', x, r)
        return r
    return inner
