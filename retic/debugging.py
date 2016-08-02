from . import visitors
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
