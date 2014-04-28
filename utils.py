import ast
import typing, flags
from exc import UnknownTypeError

def copy_assignee(n, ctx):
    if isinstance(n, ast.Name):
        ret = ast.Name(id=n.id, ctx=ctx)
    elif isinstance(n, ast.Attribute):
        ret = ast.Attribute(value=n.value, attr=n.attr, ctx=ctx)
    elif isinstance(n, ast.Subscript):
        ret = ast.Subscript(value=n.value, slice=n.slice, ctx=ctx)
    elif isinstance(n, ast.List):
        elts = [copy_assignee(e, ctx) for e in n.elts]
        ret = ast.List(elts=elts, ctx=ctx)
    elif isinstance(n, ast.Tuple):
        elts = [copy_assignee(e, ctx) for e in n.elts]
        ret = ast.Tuple(elts=elts, ctx=ctx)
    elif isinstance(n, ast.Starred):
        ret = ast.Starred(value=copy_assignee(n.value, ctx), ctx=ctx)
    elif isinstance(n, ast.Call):
        args = [copy_assignee(e, ctx) for e in n.args]
        ret = ast.Call(func=n.func, args=args, keywords=n.keywords, starargs=n.starargs, kwargs=n.kwargs)
    else: return n
    ast.copy_location(ret, n)
    return ret

def iter_type(ty):
    if isinstance(ty, typing.List):
        return ty.type
    else: return typing.Dyn

def handle_static_type_error(error, exit=True):
    print('\nReticulated has detected a')
    print('====STATIC TYPE ERROR=====')
    print('Message:')
    print(*error.args)
    print()
    if exit:
        quit()
