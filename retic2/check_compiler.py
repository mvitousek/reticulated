## This module is used to translate from an internal representation of
## transient checks, where they're represented with the
## retic_ast.Check node, into a regular Python representation that can
## be outputted or executed.

from . import copy_visitor, retic_ast, ast_trans
import ast

check_function = '__retic_check'

class CheckCompiler(copy_visitor.CopyVisitor):
    examine_functions = True

    def visitCheck(self, n, *args):
        val = self.dispatch(n.value)
        return ast_trans.Call(func=ast.Name(id=check_function, ctx=ast.Load(), lineno=n.lineno, col_offset=n.col_offset),
                              args=[val, n.type.to_ast(lineno=val.lineno, col_offset=val.col_offset)], keywords=[], starargs=None,
                              kwargs=None, lineno=val.lineno, col_offset=val.col_offset)
            
