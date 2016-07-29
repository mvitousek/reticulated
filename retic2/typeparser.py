from . import retic_ast, exc
from .astor import codegen
import ast

def unparse(n:ast.expr)->str:
    return codegen.to_source(n)

def typeparse(n)->retic_ast.Type:
    if n is None:
        return retic_ast.Dyn()
    elif isinstance(n, ast.Name):
        if n.id == 'int':
            return retic_ast.Int()
        elif n.id == 'bool':
            return retic_ast.Bool()
        elif n.id == 'str':
            return retic_ast.Str()
        elif n.id == 'None':
            return retic_ast.Void()
        elif n.id == 'Any':
            return retic_ast.Dyn()
        else: raise exc.MalformedTypeError(n, '{} is not a valid type name'.format(n.id))
    elif isinstance(n, ast.Call):
        if isinstance(n.func, ast.Name):
            if n.func.id == 'Function':
                if len(n.args) != 2:
                    raise exc.MalformedTypeError(n, 'Function constructors take only two arguments')
                else:
                    src = argparse(n.args[0])
                    trg = typeparse(n.args[1])
                    return retic_ast.Function(src, trg)
            else: raise exc.UnimplementedException()
        else:
            raise exc.MalformedTypeError(n, '{} is not a valid type construct'.format(unparse(n)))
    elif isinstance(n, ast.Subscript):
        if isinstance(n.value, ast.Name):
            if n.id == 'List':
                if not isinstance(n.slice, ast.Index):
                    raise exc.MalformedTypeError(n, 'List constructors take only the type of list elements')
                else:
                    elts = typeparse(n.slice.value)
                    return retic_ast.List(elts)
            else: raise exc.UnimplementedException()
        else: raise exc.MalformedTypeError(n, '{} is not a valid type construct'.format(unparse(n)))
    else: raise exc.UnimplementedException()
        
def argparse(n: ast.expr) -> retic_ast.ArgTypes:
    if isinstance(n, ast.List):
        tys = [typeparse(elt) for elt in n.elts]
        return retic_ast.PosAT(tys)
    elif isinstance(n, ast.Ellipsis):
        return retic_ast.ArbAT()
    else: raise exc.MalformedTypeError(n, '{} is not a valid function parameter type specification'.format(unparse(n)))
