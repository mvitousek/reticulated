from copy_visitor import CopyVisitor
from typecheck import fixup
import ast

class IdentityReplacementVisitor(CopyVisitor):
    def unproxy(self, n):
        return fixup(ast.Call(func=ast.Name(id='retic_actual', ctx=ast.Load()),
                              args=[n], keywords=[], starargs=None, kwargs=None, lineno=n.lineno,
                              col_offset=n.col_offset))

    def visitCompare(self, n):
        left = self.dispatch(n.left)
        rcomparators = self.reduce(n.comparators)
        lcomparators = [left] + comparators
        comparators = []
        last_was_is = False
        for index, op in enumerate(n.ops):
            is_is = isinstance(op, ast.Is)
            if is_is or last_was_is:
                comparators.append(self.unproxy(lcomparators[index]))
            else: comparators.append(lcomparators[index])
            last_was_is = is_is
        left = comparators[0]
        comparators = comparators[1:]
        return ast.Compare(left=left, ops=n.ops, comparators=comparators)

class MonotonicAttributeVisitor(CopyVisitor):
    def getter(self, n, static):
        pass
   
    def visitAttribute(self, n):
        if not isinstance(n.ctx, ast.Store) and not isinstance(n.ctx, ast.Del):
            pass
