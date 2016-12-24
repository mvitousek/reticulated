from . import retic_ast

def simple_subtype_meet(t1, t2):
    """
    Recieves two retic types and returns the intersection
    """

    if isinstance(t1, retic_ast.Instance) and\
       isinstance(t2, retic_ast.Instance):

        if classes_eq(t1.instanceof, t2.instanceof):
            return t1

        #transtitive closure
        elif in_inherit(t2.instanceof.inherits, t1):
            return t2

        elif in_inherit(t1.instanceof.inherits, t2):
            return t1

        else:
            return retic_ast.Bot()

    elif isinstance(t1, retic_ast.Dyn) and \
            isinstance(t2, retic_ast.Dyn):
        return t1

    elif isinstance(t1, retic_ast.Dyn):
        return t2

    elif isinstance(t2, retic_ast.Dyn):
        return t1

    elif t1 == t2:
        return t1

    elif isinstance(t1, retic_ast.List) and \
            isinstance(t2, retic_ast.TopList):
            return t1

    elif isinstance(t2, retic_ast.List) and \
            isinstance(t1, retic_ast.TopList):
            return t2

    elif isinstance(t1, retic_ast.Tuple) and\
            isinstance(t2, retic_ast.TopTuple):
            return t1

    elif isinstance(t2, retic_ast.Tuple) and\
            isinstance(t1, retic_ast.TopTuple):
            return t2

    elif isinstance(t1, retic_ast.Set) and\
            isinstance(t2, retic_ast.TopSet):
            return t1

    elif isinstance(t2, retic_ast.Set) and\
            isinstance(t1, retic_ast.TopSet):
            return t2

    elif isinstance(t1, retic_ast.Union):
        return handle_union(t1, t2)

    elif isinstance(t2, retic_ast.Union):
        return handle_union(t2, t1)

    elif isinstance(t1, retic_ast.TopFunction) and\
            isinstance(t2, retic_ast.Function):
        return t2

    elif isinstance(t2, retic_ast.TopFunction) and\
            isinstance(t1, retic_ast.Function):
        return t1

    elif isinstance(t1, retic_ast.Instance) and\
        isinstance(t2, retic_ast.TopFunction):
        cls = t1.instanceof
        if "__call__" in cls.members:
            return t1
        else:
            return retic_ast.Bot()

    elif isinstance(t2, retic_ast.Instance) and\
        isinstance(t1, retic_ast.TopFunction):
        cls = t2.instanceof
        if "__call__" in cls.members:
            return t2
        else:
            return retic_ast.Bot()

    else:
        return retic_ast.Bot()


def handle_union(union_type, t2):
    new_alt = []
    for ty in union_type.alternatives:
        glb = simple_subtype_meet(ty, t2)
        if not isinstance(glb, retic_ast.Bot):
            new_alt.append(glb)
    if len(new_alt) == 0:
        res_type = retic_ast.Bot()
    elif len(new_alt) == 1:
        res_type = new_alt[0]
    elif len(new_alt) > 1:
        res_type = retic_ast.Union(new_alt)
    return res_type


def in_inherit(items, element):
    for item in items:
        if classes_eq(item, element.instanceof):
            return True

        elif in_inherit(item.inherits, element):
            return True
    return False

def classes_eq(inst1, inst2):
    """
    Checks if two instances are equal
    :param inst1: Class
    :param inst2: Class
    :return: boolean
    """
    return inst1.name == inst2.name


