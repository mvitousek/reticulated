import ast
import retic.typeparser
from . import exc
from retic.proposition import *

def extract_prop(an_ast, aliases):
    """
    :param an_ast: Ast Expression
    :return: Proposition

    ors, ands, nots, is intance
    """
    if isinstance(an_ast,  ast.BoolOp):
        op = get_op(an_ast.op)
        return get_bool_prop(an_ast.values, op, aliases)
    elif is_instance_node(an_ast):
            return get_isinstance_prop(an_ast, aliases)
    else:
        return TrueProp()

def get_bool_prop(is_inst_list, op, aliases):
    """
    generates a proposition from isinstance list
    :param is_inst_list: [Ast, ...]
    :param op: operation to wrap around the list
    :return: [Proposition, ...]
    """
    res = []
    for inst in is_inst_list:
        res.append(extract_prop(inst, aliases))
    return op(res)

def get_op(op):
    """
    Gets proposition class from ast OP
    :param op: ast OP
    :return: proposition class
    """
    if isinstance(op, ast.And):
        return AndProp
    elif isinstance(op, ast.Or):
        return OrProp
    elif isinstance(op, ast.Not):
        return NotProp


def is_instance_node(an_ast):
    """
    Determines if AST is an isinstance with a length of 2
    :param an_ast: Test AST node
    :return: Bool
    """
    # if isinstance(an_ast, ast.Expr):
    #     val = an_ast.value
    if isinstance(an_ast, ast.Call):
        return an_ast.func.id == 'isinstance' and \
               len(an_ast.args) == 2

def get_isinstance_prop(isinstance_ast, aliases):
    """
    gets an ast prop out of ast
    :param isinstance_ast: ast
    :return: Proposition
    """
    args = isinstance_ast.args
    var = args[0].id
    t = get_valid_inst_type(isinstance_ast, aliases)
    return PrimP(var, t)

def get_valid_inst_type(inst_ast, aliases):
    """
    Given an is_inst AST, generates the appropriate type
    :param inst_ast: AST
    :return: retic type
    """
    args = inst_ast.args
    try:
        t = typeparse(args[1], aliases)
    except exc.MalformedTypeError:
        if args[1].id == 'list':
            t = TopList()
        else:
            t = TrueProp()
    return t




