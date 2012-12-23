import vis, type_helpers

class Typechecker(Vistor):
    def typecheck(self, n):
        self.preorder(n, [])

    def visitFunctionDef(self, n):
        
