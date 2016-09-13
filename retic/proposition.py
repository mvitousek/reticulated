import sympy
import uuid
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
        - generate the reminder of the Proposition

        :param type_env: the type environment
        :return: type_env', Proposition
        """
        pass


    def transform_and_reduce(self, transformer, *args):
        """
        returns a simplified sympy formula and a set of mappings
        from sympy.Symbol -> Proposition
        :return (formula, map)
        """
        pass

    def transform_back(self):
        """
        Transforms a sympy formula to a Proposition
        :return Proposition
        """
        pass


class Prim_P(Proposition):
    """
    Represents the ways we can represent information about a type
    in python
    Prim_p("x", int) is the proposition: x is of type int.

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

    def transform_and_reduce(self, transformer, *args):
        if not transformer:
            my_str = str(uuid.uuid3(uuid.NAMESPACE_DNS, self.__str__()))
        else:
            my_str = str(transformer(*args))
        f = Symbol(my_str)
        return f, {f: self}

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.var == other.var and self.type == other.type

    def __hash__(self):
        return hash(self.var) ^ hash(self.type)

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
        Proposition.__init__(self)
        self.operands = operands

    def transform_and_reduce(self, transformer, *args):
        formulea, type_map = [],{}
        for op in self.operands:
            formula, m = op.transform_and_reduce(transformer, *args)
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

    def transform(self, type_env):
        pass

    def get_op(self):
        return And

class OrProp(OpProp):
    def __init__(self, operands):
        OpProp.__init__(self, operands)

    def transform(self, type_env):
        pass

    def get_op(self):
        return Or

class NotProp(OpProp):
    def __init__(self, operand):
        """
        :param operand: Single operand only!
        """
        OpProp.__init__(self, [operand])

    def transform(self, type_env):
        pass

    def get_op(self):
        return Not


class Done(Proposition):
    pass

