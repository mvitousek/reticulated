from .. import visitors
from . import constraints, ctypes
import ast

class OpenWorld(visitors.SetGatheringVisitor):
    examine_functions = False

    def visitClassDef(self, n, *args):
        st = super().visitClassDef(n, *args)
        return st | {constraints.STC(n.retic_ctype, ctypes.CDyn())}
    
    def visitFunctionDef(self, n, *args):
        args = [arg.retic_ctype for arg in n.args.args]
        return {constraints.STC(ctypes.CDyn(), argty) for argty in args} | {constraints.STC(n.retic_return_ctype, ctypes.CDyn())}

    def visitName(self, n, *args):
        if isinstance(n.ctx, ast.Store):
            return {constraints.STC(n.retic_ctype, ctypes.CDyn()),
                    constraints.STC(ctypes.CDyn(), n.retic_ctype)}
        else:
            return set()
    
