import sympy
from retic.constants import types_dict
from copy import copy
from sympy.logic import simplify_logic
from sympy import Symbol
from sympy import Or, And, Not


class Proposition:
    """
    A propositional formula that gives us information about variables and
    their types
    """
    def __init__(self):
        pass

    def transform(self, type_env):
        """
        Transforms this formula such that:
        - type_env is extended from var -> types
        - generate the reminder of the formula

        :param type_env: the type environment
        :return: type_env', Proposition
        """
        pass

    def simplify(self):
        """
        - Transforms to a formula
        - Reduces formula
        - Transforms back the reduced prop.
        """
        pass

    def transform_and_reduce(self):
        """
        :return (formula, map)
        """
        pass

    def transform_back(self):
        """
        :return Proposition
        """
        pass


class Prim_P(Proposition):
    """
    Represents the ways we can represent information about a type
    in python

    """
    def __init__(self, var, type):
        """
        :param var: string
        :param type: Python type
        """
        Proposition.__init__(self)
        self.var = var
        self.type = type

    def transform(self, type_env):
        pass

    def transform_and_reduce(self):
        f = Symbol('%s is of type %s' % (self.var, self.type))
        return f, {(f, self)}

    def simplify(self):
        return self


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
        Proposition.__init__(self)
        self.operands = operands

    def transform_and_reduce(self):
        res, type_map = [], set()
        for op in self.operands:
            (r, m) = op.transform_and_reduce()
            res.append(r)
            type_map = type_map.union(m)

        prop_op = self.get_op()
        return simplify_logic(prop_op(*res)), type_map

class AndProp(OpProp):
    def __init__(self, operands):
        OpProp.__init__(self, operands)

    def transform(self, type_env):
        pass

    def simplify(self):
        pass

    def get_op(self):
        return And


class Done(Proposition):
    pass

