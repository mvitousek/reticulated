import ast
from copy import copy
from . import retic_ast

def get_test_env(node, env):
    """
    :param node: test node
    :param env: dict
    :return: (ast.node, dict)
    """
    test_env, orelse = copy(env), copy(env)
    if isinstance(node, ast.Expr):
        if node.value == ast.Call and node.func.id == 'isinstance':
            args = node.value.args
            var = args[0].id
            val = args[1].id
            test_env[var] = val

            or_else_type = env[var]
            if isinstance(or_else_type, retic_ast.Union):
                orelse[var].alternatives.remove(val)

    return test_env, orelse




# print(ast.dump(ast.parse('isinstance(x, int)')))
#
# p = ast.parse('isinstance(x, int)')
# print(p.body[0].value.args[1].id)



# Call(func=Name(id='isinstance', ctx=Load()), args=[Name(id='x', ctx=Load()), Name(id='int', ctx=Load())], keywords=[], starargs=None, kwargs=None)
