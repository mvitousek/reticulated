## This module is used to expand the prebuilt macros provided by Reticulated

from . import copy_visitor, retic_ast, ast_trans
import ast


class MacroExpander(copy_visitor.CopyVisitor):
    examine_functions = True

    def visitCall(self, n, *args):
        if isinstance(n.func, ast.Name):
            if n.func.id == '__typeof':
                return ast.Str(s=str(n.args[0].retic_type))
            else:
                return super().visitCall(n)
        else: return super().visitCall(n)
