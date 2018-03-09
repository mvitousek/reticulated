from .. import visitors, consistency, retic_ast, exc
from . import constraints, ctypes

class ReturnConstraintGenerator(visitors.SetGatheringVisitor):
    ## This visitor looks at function return values and reports an error if either
    ## - A function can return a value that doesn't correspond to the
    ##   function's annotated return type
    ## - Not all paths through a function lead to either an exception
    ##   being raised or a value being returned.

    def visitModule(self, n):
        return self.dispatch_statements(n.body, None)
    
    def visitFunctionDef(self, n, retty, *args):        
        return self.dispatch_statements(n.body, n.retic_return_ctype, *args)

    def visitClassDef(self, n, retty, *args):
        return self.dispatch_statements(n.body, None, *args)

    def visitReturn(self, n, retty, *args):
        if n.value:
            ty = n.value.retic_ctype
        else: 
            ty = ctypes.CVoid()
        if retty is not None:
            return {constraints.STC(ty, retty)}
        else: return set()
