from retic import retic_ast

types_dict = {
            int: retic_ast.Int,
            float: retic_ast.Float,
            str: retic_ast.Str,
            bool: retic_ast.Bool,
            list: retic_ast.List,
            tuple: retic_ast.Tuple,
}

