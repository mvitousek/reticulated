from . import visitors
import ast

class LocationFreeFinder(visitors.BooleanOrVisitor):
    examine_functions = True
    def dispatch(self, val, *args):
        if (not hasattr(val, 'lineno') or val.lineno is None) and isinstance(val, ast.expr):
            raise Exception(val.__class__, ast.dump(val))
        super().dispatch(val, *args)

class MissingTypeFinder(visitors.BooleanOrVisitor):
    examine_functions = True
    def dispatch(self, val, *args):
        if isinstance(val, ast.expr) and not hasattr(val, 'retic_type'): 
            raise Exception(val.__class__, ast.dump(val))
        return super().dispatch(val, *args)
