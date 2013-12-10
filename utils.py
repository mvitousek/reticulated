import ast
import typing

def copy_assignee(n, ctx):
    if isinstance(n, ast.Name):
        ret = ast.Name(id=n.id, ctx=ctx)
    elif isinstance(n, ast.Attribute):
        ret = ast.Attribute(value=n.value, attr=n.attr, ctx=ctx)
    elif isinstance(n, ast.Subscript):
        ret = ast.Subscript(value=n.value, slice=n.slice, ctx=ctx)
    elif isinstance(n, ast.List):
        ret = ast.List(elts=n.elts, ctx=ctx)
    elif isinstance(n, ast.Tuple):
        ret = ast.Tuple(elts=n.elts, ctx=ctx)
    elif isinstance(n, ast.Starred):
        ret = ast.Starred(value=n.value, ctx=ctx)
    ast.copy_location(ret, n)
    return ret

def iter_type(ty):
    if isinstance(ty, typing.List):
        return ty.type
    else: return typing.Dyn
