import sympy
from . import retic_ast
from retic.counter import gen_nums
from copy import copy
from sympy.logic import simplify_logic, true
from sympy import Symbol
from sympy import Or, And, Not
from retic.typeparser import typeparse

import itertools

#count
f = gen_nums(0)

class Proposition:
    """
    A propositional formula that gives us information about variables and
    their types
    """
    def __init__(self):
        pass

    def transform(self, type_env, aliases):
        """
        Transforms this formula such that:
        - type_env is extended from var -> types
        - generate the reminder of the Proposition
        - Expect a simplified proposition

        :param type_env: the type environment
        :param aliases: Scope of types
        :type aliases: {Str -> Types}
        :return: type_env', Proposition
        """
        raise NotImplementedError("Method not yet implemented")


    def transform_and_reduce(self, type_map):
        """
        returns a simplified sympy formula and a type map
        :param type_map: Maps Propositoins to Symbols
        :type type_map: type_map:  {PrimP: Symbol, ....}
        :return (Sympy formula, map)
        """
        raise NotImplementedError("Method not yet implemented")

    def simplify(self, type_map):
        """
        returns a simplified version of this formula
        :type type_map:  {PrimP: Symbol, ....}
        :return: None
        """
        formula, t_map = self.transform_and_reduce(type_map)
        return self.transform_back(formula, t_map)


    @staticmethod
    def transform_back(formula, type_map):
        """
        Transforms a sympy formula to a Proposition,
        given a type map. Inverts the type dict.
        Which is ok bec. it's 1:1
        :return Proposition
        """

        ivd = {v: k for k, v in type_map.items()}
        if isinstance(formula, Symbol):
            return ivd[formula]
        else:
            res = [Proposition.transform_back(f, type_map) for f in formula.args]
            if isinstance(formula, And):
                return AndProp(res)
            elif isinstance(formula, Or):
                return OrProp(res)
            elif isinstance(formula, Not):
                return NotProp(res[0])


class PrimP(Proposition):
    """
    Represents the ways we can represent information about a type
    in python
    PrimP("x", int) is the proposition: x is of type int.

    """
    def __init__(self, var, type):
        """
        :param var: string
        :param type: Python type
        """
        self.var = var
        assert isinstance(type, retic_ast.Type)
        self.type = type
        Proposition.__init__(self)

    def transform(self, type_env, aliases):
        type_env[self.var]=self.type
        return TrueProp(), type_env

    def transform_and_reduce(self, type_map):
        if self in type_map.keys():
            return type_map[self], type_map
        else:
            sym = Symbol(str(f()))
            type_map[self] = sym
            return sym, type_map

    def __eq__(self, other):
        return isinstance(other, PrimP) and self.var == other.var and self.type == other.type

    def __hash__(self):
        return hash(str(self))

    def __str__(self):
        return "%s,%s" % (self.var, self.type)


class OpProp(Proposition):
    """
    - Not P
    - P or P
    - P and P
    """
    def __init__(self, operands):
        """
        :param operands: list of of operands
        """
        self.operands = operands
        Proposition.__init__(self)


    def transform(self, type_env, aliases):
        return self, type_env

    def transform_and_reduce(self, type_map):
        formulea = []
        for op in self.operands:
            formula, m = op.transform_and_reduce(type_map)
            type_map.update(m)
            formulea.append(formula)

        prop_op = self.get_op()
        simplified = simplify_logic(prop_op(*formulea))
        return simplified, type_map

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.operands == other.operands

    def __hash__(self):
        return hash(self.operands)


class AndProp(OpProp):
    def __init__(self, operands):
        OpProp.__init__(self, operands)

    def transform(self, type_env, aliases):
        #if primp, we move it, else, keep in And
        rems = []
        for op in self.operands:
            (rem, type_env) = op.transform(type_env, aliases)
            if not isinstance(rem, TrueProp):
                rems.append(rem)
        if len(rems) > 1:
            return AndProp(rems), type_env
        elif len(rems) == 1:
            return rems[0], type_env
        else:
            return TrueProp(), type_env

    def get_op(self):
        return And


class OrProp(OpProp):
    def __init__(self, operands):
        OpProp.__init__(self, operands)

    def get_op(self):
        return Or


class NotProp(OpProp):
    def __init__(self, operand):
        """
        :param operand: Single operand only of type Primp
        """
        OpProp.__init__(self, [operand])

    def transform(self, type_env, aliases):
        prim_prop = self.operands[0]
        assert isinstance(prim_prop, PrimP)
        v = prim_prop.var
        t = prim_prop.type
        if v in type_env:
            if type_env[v] == t:
                del type_env[v]
            elif isinstance(type_env[v], retic_ast.Union):
                if t in type_env[v].alternatives:
                    type_env[v].alternatives.remove(t)
                    if len(type_env[v].alternatives) == 1:
                        type_env[v] = type_env[v].alternatives[0]
            # print(type_env['x'])
            return TrueProp(), type_env
        else:
            return self, type_env


    def __str__(self):
        return "Not %s" % str(self.operands[0])


    def get_op(self):
        return Not


class TrueProp(Proposition):
    def __init__(self):
        Proposition.__init__(self)

    def simplify(self, type_map):
        return self

    def transform_and_reduce(self, type_map):
        return true, type_map

    def transform_back(formula, type_map):
        return self

    def transform(self, type_env, aliases):
        return self, type_env

    def __eq__(self, other):
        return isinstance(other, TrueProp)


