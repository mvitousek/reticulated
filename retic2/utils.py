import ast
from . import exc

# Miscellaneous stuff

opnames = {
    ast.Add: 'add',
    ast.Sub: 'subtract',
    ast.Mult: 'multiply',
    ast.Div: 'divide',
    ast.Mod: 'modulo',
    ast.Pow: 'exponentiate',
    ast.LShift: 'left shift',
    ast.RShift: 'right shift',
    ast.BitOr: 'bitwise or',
    ast.BitXor: 'bitwise xor',
    ast.BitAnd: 'bitwise and',
    ast.FloorDiv: 'integer divide',
    ast.Invert: 'invert',
    ast.Not: 'logically negate',
    ast.UAdd: 'add',
    ast.USub: 'numerically negate'
}

oppasttenses = {
    ast.Mult: 'multiplied',
    ast.BitOr: 'bitwise or\'d',
    ast.BitXor: 'bitwise xor\'d'
}

def get_oppasttense(opclass)->str:
    if opclass in oppasttenses:
        return oppasttenses[opclass]
    else:
        name = opnames[opclass]
        if name[-1] == 'e':
            return name + 'd'
        else: return name + 'ed'

def stringify(op, kind:str='PRESENTTENSE')->str:
    if kind == 'PRESENTTENSE':
        return opnames[op.__class__]
    elif kind == 'PASTTENSE':
        return get_oppasttense(op.__class__)
    else: raise exc.UnimplementedException(kind)
