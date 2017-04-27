from .. import copy_visitor, retic_ast
import ast

def gensymmer():
    n = -1
    while True:
        n += 1
        yield n

gensym = gensymmer()

def genvar(annot):
    if annot is None:
        annot = ast.Name(id='Any', ctx=ast.Load())
        
    if not isinstance(annot, ast.Subscript) or not isinstance(annot.value, ast.Name) or \
       annot.value.id not in ['Trusted', 'FlowVariable']:
        annot = ast.Subscript(value=ast.Name(id='FlowVariable', ctx=ast.Load()),
                              slice=ast.Index(value=ast.Tuple(elts=[annot, ast.Num(n=next(gensym))],
                                                              ctx=ast.Load())),
                              ctx=ast.Load())

    return annot

class VariableInserter(copy_visitor.CopyVisitor):
    examine_functions = True

    def visitarg(self, n):
        return ast.arg(arg=n.arg, annotation=genvar(n.annotation))

    def visitFunctionDef(self, n):
        n = super().visitFunctionDef(n)
        n.returns = genvar(n.returns)
        return ast.fix_missing_locations(n)
