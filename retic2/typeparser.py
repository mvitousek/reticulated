from . import retic_ast, exc, flags
from .astor import codegen
import ast

# This module takes an AST representation of type annotations as
# written by the programmer and produces a retic_ast.Type for
# Reticulated's internal representation of that type. It raises a
# MalformedTypeError if the annotation is unrecognizable.

def unparse(n:ast.expr)->str:
    return codegen.to_source(n)

def typeparse(n)->retic_ast.Type:
    if n is None:
        return retic_ast.Dyn()
    elif isinstance(n, ast.NameConstant):
        if n.value == None:
            return retic_ast.Void()
        else: raise exc.MalformedTypeError(n, '{} is not a valid type name'.format(n.value))
    elif isinstance(n, ast.Name):
        if n.id == 'int':
            return retic_ast.Int()
        elif n.id == 'float':
            return retic_ast.Float()
        elif n.id == 'bool':
            return retic_ast.Bool()
        elif n.id == 'str':
            return retic_ast.Str()
        elif n.id == 'None':
            return retic_ast.Void()
        elif n.id == 'Any':
            return retic_ast.Dyn()
        elif n.id == 'Dyn':
            if flags.strict_annotations():
                raise exc.MalformedTypeError(n, 'The Dyn type is deprecated. Instead, use Any')
            return retic_ast.Dyn()
        elif n.id == 'Int':
            if flags.strict_annotations():
                raise exc.MalformedTypeError(n, 'The Int type is deprecated. Instead, use int')
            return retic_ast.Int()
        elif n.id == 'Float':
            if flags.strict_annotations():
                raise exc.MalformedTypeError(n, 'The Float type is deprecated. Instead, use float')
            return retic_ast.Float()
        elif n.id == 'String':
            if flags.strict_annotations():
                raise exc.MalformedTypeError(n, 'The String type is deprecated. Instead, use str')
            return retic_ast.String()
        elif n.id == 'Void':
            if flags.strict_annotations():
                raise exc.MalformedTypeError(n, 'The Void type is deprecated. Instead, use None')
            return retic_ast.Void()
        else: raise exc.MalformedTypeError(n, '{} is not a valid type name'.format(n.id))
    elif isinstance(n, ast.Call):
        if isinstance(n.func, ast.Name):
            if n.func.id == 'Function':
                if len(n.args) != 2:
                    raise exc.MalformedTypeError(n, 'Function constructors take only two arguments')
                elif flags.strict_annotations():
                    raise exc.MalformedTypeError(n, 'The Function constructor is deprecated. Instead, use Callable[{}, {}]'.unparse(n.args[0], n.args[1]))
                else:
                    src = argparse(n.args[0])
                    trg = typeparse(n.args[1])
                    return retic_ast.Function(src, trg)
            else: raise exc.UnimplementedException('Type definition', unparse(n))
        else:
            raise exc.MalformedTypeError(n, '{} is not a valid type construct'.format(unparse(n)))
    elif isinstance(n, ast.Subscript):
        if isinstance(n.value, ast.Name):
            if n.value.id == 'List':
                if not isinstance(n.slice, ast.Index):
                    raise exc.MalformedTypeError(n, 'List constructors take only the type of list elements')
                else:
                    elts = typeparse(n.slice.value)
                    return retic_ast.List(elts)
            elif n.value.id == 'Callable':
                if len(n.args) != 2:
                    raise exc.MalformedTypeError(n, 'Callable constructors take only two arguments')
                else:
                    src = argparse(n.args[0])
                    trg = typeparse(n.args[1])
                    return retic_ast.Function(src, trg)
            else: raise exc.UnimplementedException('Type definition', unparse(n))
        else: raise exc.MalformedTypeError(n, '{} is not a valid type construct'.format(unparse(n)))
    else: raise exc.UnimplementedException('Type definition', unparse(n))
        
def argparse(n: ast.expr) -> retic_ast.ArgTypes:
    if isinstance(n, ast.List):
        tys = [typeparse(elt) for elt in n.elts]
        return retic_ast.PosAT(tys)
    elif isinstance(n, ast.Ellipsis):
        return retic_ast.ArbAT()
    else: raise exc.MalformedTypeError(n, '{} is not a valid function parameter type specification'.format(unparse(n)))
