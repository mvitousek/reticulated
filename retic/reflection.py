import ast, rtypes, relations

def is_reflective(n: ast.Call):
    return isinstance(n.func, ast.Name) and\
        n.func.id in ['reflect_type', 'reflect_subcompat']

def reflect(n: ast.Call, env, misc, typechecker):
    assert isinstance(n, ast.Call)
    assert isinstance(n.func, ast.Name)
    
    if n.func.id == 'reflect_type':
        assert len(n.args) == 1 and not (n.keywords or n.starargs or n.kwargs)
        _, ty = typechecker.dispatch(n.args[0], env, misc)
        return ty.to_ast(), rtypes.Dyn()
    elif n.func.id == 'reflect_subcompat':
        assert len(n.args) == 2 and not (n.keywords or n.starargs or n.kwargs)
        _, ty1 = typechecker.dispatch(n.args[0], env, misc)
        _, ty2 = typechecker.dispatch(n.args[1], env, misc)
        return ast.NameConstant(value=relations.subcompat(ty1, ty2)), rtypes.Dyn()
    else: raise Exception('No valid reflective call')
