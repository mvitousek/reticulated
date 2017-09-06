from . import retic_ast, exc, flags
from .astor import codegen
import ast

# This module takes an AST representation of type annotations as
# written by the programmer and produces a retic_ast.Type for
# Reticulated's internal representation of that type. It raises a
# MalformedTypeError if the annotation is unrecognizable.

def unparse(n:ast.expr)->str:
    return codegen.to_source(n)

type_names = ['int', 'str', 'float', 'bool', 'complex', 'str', 'Any', 'None', 'Void', 'Callable', 'Tuple', 'List', 'fields', 'members', 'Dict', 'Set', 'Union', 'positional']
if not flags.strict_annotations():
    type_names += ['Dyn', 'Int', 'Float', 'String', 'Complex', 'Bool', 'Function']


def strip_prefix(n):
    if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name) and n.value.id == 'typing':
        return ast.Name(id=n.attr, ctx=ast.Load(), lineno=n.lineno, col_offset=n.col_offset)
    return n

# change the name :(
def typeparse(n, aliases)->retic_ast.Type:
    n = strip_prefix(n)
    if n is None:
        return retic_ast.Dyn()
    elif isinstance(n, ast.Str):
        return handle_str(n, aliases)
    elif flags.PY3_VERSION >= 4 and isinstance(n, ast.NameConstant):
        return handle_name_const(n, aliases)
    elif isinstance(n, ast.Name):
        return handle_name(n, aliases)
    elif isinstance(n, ast.Call):
        return handle_call(n, aliases)
    elif isinstance(n, ast.Subscript):
        return handle_subscript(n, aliases)
    elif isinstance(n, ast.Attribute):
        return parse_import_alias(n, aliases)
    elif isinstance(n, ast.Tuple):
        return handle_tuple(n, aliases)
    elif isinstance(n, ast.Dict):
        keys = []
        for key in n.keys:
            if not isinstance(key, ast.Str):
                raise exc.MalformedTypeError(key, '{} is not a valid attribute name. Attribute names in interface types must be strings.'.format(unparse(key)))
            elif key.s in keys:
                raise exc.MalformedTypeError(n, 'Duplicate definition in interface type for attribute {}'.format(key.s))
            else:
                keys.append(key.s)
        return retic_ast.Structural({k: typeparse(v, aliases) for k, v in zip(keys, n.values)})
    elif isinstance(n, retic_ast.Type):
        return n
    else: raise exc.MalformedTypeError(n, '{} is not a valid type construct'.format(unparse(n)))

def handle_str(n, aliases):
    try:
        if len(n.s) > 0 and len(ast.parse(n.s).body) > 0 and isinstance(ast.parse(n.s).body[0], ast.Expr):
            return typeparse(ast.parse(n.s).body[0].value, aliases)
        else:
            raise exc.MalformedTypeError(n, '{} is not a valid type'.format(n.s))
    except TypeError:
        raise exc.MalformedTypeError(n, '{} is not a valid type'.format(n.s))
    except ValueError:
        raise exc.MalformedTypeError(n, '{} is not a valid type'.format(n.s))
    except SyntaxError:
        raise exc.MalformedTypeError(n, 'String "{}" is not a valid type, but is used as a forward pointer'.format(n.s))

def handle_name_const(n, aliases):
    if n.value == None:
        return retic_ast.Void()
    else: raise exc.MalformedTypeError(n, '{} is not a valid type name'.format(n.value))

def handle_name(n, aliases):
    if n.id in aliases:
        return aliases[n.id]
    elif n.id == 'int':
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
            raise exc.MalformedTypeError(n, 'The Dyn type annotation is deprecated. Instead, use Any')
        return retic_ast.Dyn()
    elif n.id == 'Int':
        if flags.strict_annotations():
            raise exc.MalformedTypeError(n, 'The Int type annotation (with a capital "I") is deprecated. Instead, use int')
        return retic_ast.Int()
    elif n.id == 'Float':
        if flags.strict_annotations():
            raise exc.MalformedTypeError(n, 'The Float type annotation (with a capital "F") is deprecated. Instead, use float')
        return retic_ast.Float()
    elif n.id == 'String':
        if flags.strict_annotations():
            raise exc.MalformedTypeError(n, 'The String type annotation is deprecated. Instead, use str')
        return retic_ast.Str()
    elif n.id == 'Void':
        if flags.strict_annotations():
            raise exc.MalformedTypeError(n, 'The Void type annotation is deprecated. Instead, use None')
        return retic_ast.Void()
    else: raise exc.MalformedTypeError(n, '{} is not a valid type name'.format(n.id))

def handle_call(n, aliases):
    nfunc = strip_prefix(n.func)
    if isinstance(nfunc, ast.Name):
        if nfunc.id == 'Function':
            return make_function(n, aliases)
        elif nfunc.id == 'List':
            return make_list(n, aliases)
        elif nfunc.id == 'Set':
            return make_set(n, aliases)
        elif nfunc.id == 'Dict':
            return make_dict(n, aliases)
        elif nfunc.id == 'Tuple':
            return make_tuple(n, aliases)
        else: raise exc.MalformedTypeError(n, '{} is not a valid type construct'.format(unparse(n)))
    else:
        raise exc.MalformedTypeError(n, '{} is not a valid type construct'.format(unparse(n)))

def handle_subscript(n, aliases):
    nval = strip_prefix(n.value)
    if isinstance(n.value, ast.Name):
        if nval.id == 'List':
            return make_sub_list(n, aliases)
        elif nval.id == 'Union':
            return make_sub_union(n, aliases)
        elif nval.id == 'Callable':
            return make_sub_callable(n, aliases)
        elif nval.id == 'Tuple':
            return make_sub_tuple(n, aliases)
        elif nval.id == 'Like':
            return make_like(n, aliases)
        else: raise exc.MalformedTypeError(n, '{} is not a valid type construct'.format(unparse(n)))
    else: raise exc.MalformedTypeError(n, '{} is not a valid type construct'.format(unparse(n)))

def handle_tuple(n, aliases):
    if flags.strict_annotations():
        raise exc.MalformedTypeError(n, 'Defining tuple types directly is deprecated. Instead, use Tuple[{}]'.format(unparse(n).strip('()')))
    else:
        return retic_ast.Tuple(*[typeparse(elt, aliases) for elt in n.elts])

def make_like(n, aliases):
    if len(n.args) != 1:
        raise exc.MalformedTypeError(n, 'Like type annotations take only one argument')
    raise exc.UnimplementedException
        

def make_function(n, aliases):
    if len(n.args) != 2:
        raise exc.MalformedTypeError(n, 'Function constructors take only two arguments')
    elif flags.strict_annotations():
        raise exc.MalformedTypeError(n, 'The Function constructor is deprecated. '
                                        'Instead, use Callable[{}, {}]'.format(unparse(n.args[0]),
                                                                               unparse(n.args[1])))
    else:
        src = argparse(n.args[0], aliases)
        trg = typeparse(n.args[1], aliases)
        return retic_ast.Function(src, trg)

def make_list(n, aliases):
    if len(n.args) != 1:
        raise exc.MalformedTypeError(n, 'List constructors take only the type of list elements')
    elif flags.strict_annotations():
        raise exc.MalformedTypeError(n, 'Using the List constructor with parentheses is deprecated. '
                                        'Instead, use List[{}]'.format(unparse(n.args[0])))
    else:
        elts = typeparse(n.args[0], aliases)
        return retic_ast.List(elts)


def make_set(n, aliases):
    if len(n.args) != 1:
        raise exc.MalformedTypeError(n, 'Set constructors take only the type of list elements')
    elif flags.strict_annotations():
        raise exc.MalformedTypeError(n, 'Using the Set constructor with parentheses is deprecated. Instead, use Set[{}]'.format(unparse(n.args[0])))
    else:
        elts = typeparse(n.args[0], aliases)
        return retic_ast.Set(elts)

def make_dict(n, aliases):
    if len(n.args) != 2:
        raise exc.MalformedTypeError(n, 'Dictionary constructors take only the types of dictionary keys and dictionary values')
    elif flags.strict_annotations():
        raise exc.MalformedTypeError(n, 'Using the Dict constructor with parentheses is deprecated. Instead, use Dict[{}, {}]'.format(unparse(n.args[0]), unparse(n.args[1])))
    else:
        keys = typeparse(n.args[0], aliases)
        vals = typeparse(n.args[1], aliases)
        return retic_ast.Dict(keys, vals)

def make_tuple(n, aliases):
    if flags.strict_annotations():
        raise exc.MalformedTypeError(n, 'Using the Tuple constructor with parentheses is deprecated.'
                                        ' Instead, use Tuple[{}]'.format(unparse(n)[6:-1]))
                                        # Should trim off "Tuple(" and ")"
    else:
        return retic_ast.Tuple(*[typeparse(elt, aliases) for elt in n.args])

def make_sub_list(n, aliases):
    if not isinstance(n.slice, ast.Index):
        raise exc.MalformedTypeError(n, 'List constructors take only the type of list elements')
    else:
        elts = typeparse(n.slice.value, aliases)
        return retic_ast.List(elts)

def make_sub_set(n, aliases):
    if not isinstance(n.slice, ast.Index):
        raise exc.MalformedTypeError(n, 'Set constructors take only the type of list elements')
    else:
        elts = typeparse(n.slice.value, aliases)
        return retic_ast.Set(elts)

def make_sub_dict(n, aliases):
    if isinstance(n.slice, ast.Index):
        if isinstance(n.slice.value, ast.Tuple):
            if len(n.slice.value.elts) != 2:
                raise exc.MalformedTypeError(n, 'Dictionary constructors take only the types of dictionary keys and dictionary values')
            else:
                keys = typeparse(n.slice.value.elts[0], aliases)
                vals = typeparse(n.slice.value.elts[1], aliases)
                return retic_ast.Dict(keys, vals)
        else:
            raise exc.MalformedTypeError(n, 'Dictionary constructors take only two arguments, as a pair within a single set of square brackets')
    else:
        raise exc.MalformedTypeError(n, 'Dictionary constructors take only two arguments, as a pair within a single set of square brackets')

def make_sub_union(n, aliases):
    if isinstance(n.slice, ast.Index):
        if isinstance(n.slice.value, ast.Tuple):
            if len(n.slice.value.elts) < 2:
                raise exc.MalformedTypeError(n, 'Not enough types in this union, '
                                                'at least 2 are required, given {}'.format(len(n.slice.value.elts)))
            else:
                #possibly prevent user from writing union of union
                alternatives = [typeparse(t, aliases) for t in  n.slice.value.elts]
                return retic_ast.Union(alternatives)
        else:
            raise exc.MalformedTypeError(n, "Expected a Tuple of at least 2 types. Got {}".format(unparse(n.slice.value)))
    else:
        raise exc.MalformedTypeError(n, "Expected a Tuple of at least 2 types. Got {}".format(unparse(n.slice)))

def make_sub_callable(n, aliases):
    if not isinstance(n.slice, ast.Index) or not isinstance(n.slice.value, ast.Tuple) or len(n.slice.value.elts) != 2:
        raise exc.MalformedTypeError(n, 'Callable constructors take only two arguments, as a pair within a single set of square brackets')
    else:
        src = argparse(n.slice.value.elts[0], aliases)
        trg = typeparse(n.slice.value.elts[1], aliases)
        return retic_ast.Function(src, trg)

def make_sub_tuple(n, aliases):
    if not isinstance(n.slice, ast.Index):
        raise exc.MalformedTypeError(n, 'Tuple constructors take only the types of tuple elements')
    elif isinstance(n.slice.value, ast.Tuple):
        if len(n.slice.value.elts) == 2 and isinstance(n.slice.value.elts[1], ast.Ellipsis):
            return retic_ast.HTuple(typeparse(n.slice.value.elts[0], aliases))
        else: return retic_ast.Tuple(*[typeparse(elt, aliases) for elt in n.slice.value.elts])
    else:
        return retic_ast.Tuple(typeparse(n.slice.value, aliases))

def argparse(n: ast.expr, aliases) -> retic_ast.ArgTypes:
    if isinstance(n, ast.List):
        tys = [typeparse(elt, aliases) for elt in n.elts]
        return retic_ast.PosAT(tys)
    elif isinstance(n, ast.Ellipsis):
        return retic_ast.ArbAT()
    else: raise exc.MalformedTypeError(n, '{} is not a valid function parameter type specification'.format(unparse(n)))

def sequentialize_attributes(n):
    if isinstance(n, ast.Name):
        if n.id == 'typing':
            return []
        return [n.id]
    elif isinstance(n, ast.Attribute):
        return sequentialize_attributes(n.value) + [n.attr]
    else: raise exc.MalformedTypeError(n, '{} is not a valid segment of a type name'.format(unparse(n)))

def parse_import_alias(n, aliases):
    seq = sequentialize_attributes(n)
    assert len(seq) > 1
    name = seq[0]
    label = name
    for elt in seq[1:]:
        if name in aliases and isinstance(aliases[name], dict):
            aliases = aliases[name]
            name = elt
            label += '.' + elt
        elif name in aliases:
            raise exc.MalformedTypeError(n, '{} is a type and does not contain type aliases'.format(label))
        else:
            raise exc.MalformedTypeError(n, '{} does not contain the type alias {}'.format(label, elt))
    if name in aliases:
        return aliases[name]
    else:
        raise exc.MalformedTypeError(n, '{} does not contain the type alias {}'.format(label, elt))
