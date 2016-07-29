from . import copy_visitor, retic_ast
import ast

class Tombstone(ast.stmt): pass

class CheckRemover(copy_visitor.CopyVisitor):
    examine_functions = True
    
    def reduce(self, ns, *args):
        lst = [self.dispatch(n, *args) for n in ns]
        return [l for l in lst if not isinstance(l, Tombstone)]

    def dispatch_scope(self, ns, *args):
        lst = [self.dispatch(s, *args) for s in ns]
        return [l for l in lst if not isinstance(l, Tombstone)]

    def dispatch_statements(self, ns, *args):
        if not hasattr(self, 'visitor'): # preorder may not have been called
            self.visitor = self
        lst = [self.dispatch(s, *args) for s in ns]
        return [l for l in lst if not isinstance(l, Tombstone)]

    def visitCheck(self, n, *args):
        val = self.dispatch(n.value)
        if isinstance(n.type, retic_ast.Dyn):
            return n.value
        else:
            return retic_ast.Check(value=val, type=n.type, lineno=n.lineno, col_offset=n.col_offset)

    def visitExpr(self, n, *args):
        val = self.dispatch(n.value)
        if isinstance(n.value, retic_ast.Check) and isinstance(val, ast.Name):
            return Tombstone()
        else:
            return ast.Expr(value=val, lineno=n.lineno)
            
