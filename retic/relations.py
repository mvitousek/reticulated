from . import retic_ast

def simple_subtype_meet(t1, t2):
    """
    Recieves two retic types and returns the intersection
    """

    if isinstance(t1, retic_ast.Instance) and\
       isinstance(t2, retic_ast.Instance) and\
        t1.instanceof.name == t2.instanceof.name:

        return t1

    elif isinstance(t1, retic_ast.Dyn) and isinstance(t2, retic_ast.Dyn):
        return t1

    elif isinstance(t1, retic_ast.Dyn):
        return t2

    elif isinstance(t2, retic_ast.Dyn):
        return t1

    elif t1 == t2:
        return t1

    elif isinstance(t1, retic_ast.List) and isinstance(t2, retic_ast.TopList):
            return t1

    elif isinstance(t2, retic_ast.List) and isinstance(t1, retic_ast.TopList):
            return t2

    elif isinstance(t1, retic_ast.Tuple) and isinstance(t2, retic_ast.TopTuple):
            return t1

    elif isinstance(t2, retic_ast.Tuple) and isinstance(t1, retic_ast.TopTuple):
            return t2

    elif isinstance(t1, retic_ast.Set) and isinstance(t2, retic_ast.TopSet):
            return t1

    elif isinstance(t2, retic_ast.Set) and isinstance(t1, retic_ast.TopSet):
            return t2

    elif isinstance(t1, retic_ast.Union):
        return handle_union(t1, t2)

    elif isinstance(t2, retic_ast.Union):
        return handle_union(t2, t1)

    else:
        return retic_ast.Bot()


def handle_union(union_type, t2):
    new_alt = []
    for ty in union_type.alternatives:
        glb = simple_subtype_meet(ty, t2)
        if not isinstance(glb, retic_ast.Bot):
            new_alt.append(ty)
    if len(new_alt) == 0:
        res_type = retic_ast.Bot()
    elif len(new_alt) == 1:
        res_type = new_alt[0]
    elif len(new_alt) > 1:
        res_type = retic_ast.Union(new_alt)
    return res_type
