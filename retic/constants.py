from retic import retic_ast

inst = 'isinstance'
types_dict = {
            #primitive (no complex????)
            'int': retic_ast.Int,
            'float': retic_ast.Float,
            'str': retic_ast.Str,
            'bool': retic_ast.Bool,
            #dicts, sets?
            'list': retic_ast.List,
            'tuple': retic_ast.Tuple,
}


