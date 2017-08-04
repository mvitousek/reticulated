from .. import copy_visitor, retic_ast, ast_trans, flags
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
        if flags.PY3_VERSION >= 4:
            lineno, col_offset = n.lineno, n.col_offset
        n = ast.arg(arg=n.arg, annotation=genvar(n.annotation))
        if flags.PY3_VERSION >= 4:
            n.lineno, n.col_offset = lineno, col_offset
        return ast.fix_missing_locations(n)
        

    def visitFunctionDef(self, n):
        lineno, col_offset = n.lineno, n.col_offset
        n = super().visitFunctionDef(n)
        n.returns = genvar(n.returns)
        n.lineno, n.col_offset = lineno, col_offset
        return ast.fix_missing_locations(n)

    def visitClassDef(self, n):
        lineno, col_offset = n.lineno, n.col_offset
        n = super().visitClassDef(n)
        n.lineno, n.col_offset = lineno, col_offset
        decs = []
        for dec in n.decorator_list:
            if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Name) and dec.func.id == 'fields':
                values = []
                for value in dec.args[0].values:
                    values.append(genvar(value))
                decs.append(ast_trans.Call(func=dec.func, args=[ast.Dict(keys=dec.args[0].keys, values=values)],
                                           keywords=dec.keywords, starargs=ast_trans.starargs(dec),
                                           kwargs=ast_trans.kwargs(dec)))
            else:
                decs.append(dec)
        return ast.fix_missing_locations(
            ast_trans.ClassDef(name=n.name, bases=n.bases, keywords=n.keywords, starargs=ast_trans.starargs(n),
                               kwargs=ast_trans.kwargs(n), body=n.body, decorator_list=decs, lineno=n.lineno,
                               col_offset=n.col_offset))
