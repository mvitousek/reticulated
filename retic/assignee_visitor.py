from . import visitors
import ast

class AssigneeVisitor(visitors.SetGatheringVisitor):
    def visitClass(self, n):
        return set([n.name])
    def visitFunction(self, n):
        return set([n.name])
    def visitName(self, n):
        if isinstance(n.ctx, ast.Store):
            return set(n.id)
        else: return set()
