import sympy
from retic.constants import types_dict
from retic.counter import gen_nums
from copy import copy
from sympy.logic import simplify_logic
from sympy import Symbol
from sympy import Or, And, Not

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

    def transform(self, type_env):
        """
        Transforms this formula such that:
        - type_env is extended from var -> types
        - generate the reminder of the Proposition
        - Expect a simplified proposition

        :param type_env: the type environment
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
        self.type = type
        Proposition.__init__(self)

    def transform(self, type_env):
        #THIS IS NOT CORRECT
        #NEED SOMETHING LIKE TYPE PARSER!!!!!!!
        var_type = types_dict[self.type]
        new_env = copy(type_env)
        new_env[self.var]=var_type
        return NoRem(), new_env

    def transform_and_reduce(self, type_map):
        if self in type_map.keys():
            return type_map[self], type_map
        else:
            sym = Symbol(str(f()))
            type_map[self] = sym
            return sym, type_map

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
        self.operands = operands
        Proposition.__init__(self)


    def transform(self, type_env):
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

    def __str__(self):
        return "%s(%s)" % (OpProp.__name__, str(self.operands))


class AndProp(OpProp):
    def __init__(self, operands):
        OpProp.__init__(self, operands)

    def transform(self, type_env):
        #if primp, we move it, else, keep in And
        rems, t_env_final = [],{}
        for op in self.operands:
            (rem, t_env) = op.transform(type_env)
            if not isinstance(rem, NoRem):
                rems.append(rem)
            t_env_final.update(t_env)
        if len(rems)>1:
            return AndProp(rems), t_env_final
        elif len(rems) == 1:
            return rems[0], t_env_final
        else:
            return NoRem(), t_env_final

    def get_op(self):
        return And


class OrProp(OpProp):
    def __init__(self, operands):
        OpProp.__init__(self, operands)

    def transform(self, type_env):
        return self, type_env

    def get_op(self):
        return Or


class NotProp(OpProp):
    def __init__(self, operand):
        """
        :param operand: Single operand only!
        """
        OpProp.__init__(self, [operand])

    def transform(self, type_env):
        #if the opp. is contained in a union then we
        #should remove it from the union.
        pass

    def get_op(self):
        return Not


class NoRem(Proposition):
    def __init__(self):
        Proposition.__init__(self)

    def simplify(self, type_map):
        raise NotImplementedError("No formula to simplify")

    def transform(self, type_env):
        return type_env, self

    def __eq__(self, other):
        return isinstance(other, NoRem)