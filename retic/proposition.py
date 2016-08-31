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
        - generate the reminder, which consists of a list of or's
          and not's

        :param type_env: the type environment
        :return: type_env', Proposition
        """
        pass

class OpProp(Proposition):
    """
    - Not P
    - P or P
    - P and P
    """
    def __init__(self, operands):
        """
        :param operands: List of [Propositions]
        """
        Proposition.__init__(self)
        self.operands = operands

class AndProp(OpProp):
    def __init__(self, operands):
        OpProp.__init__(self, operands)

    def transform(self, type_env):
        env_and_prop = [o.transform(type_env) for o in operands]

        for t in env_and_prop:
            (new_env, prop) = t

            # TODO
            # env = merge_envs(new_env, type_env)
            #
            # if isinstance(prop, Prim_P):
            #     n_env = prop.transform(env)




class OrProp(OpProp):
    def __init__(self, operands):
        OpProp.__init__(self, operands)

    def transform(self, type_env):
        pass

class NotProp(OpProp):
    def __init__(self, operand):
        OpProp.__init__(self, operand)

    def transform(self, type_env):
        pass

class Prim_P(Proposition):
    """
    Represents the ways we can represent information about a type
    in python

    """
    def __init__(self, var, type):
        """
        :param var: string??
        :param type: Python type
        """
        Proposition.__init__(self)
        self.var = var
        self.type = type

    def transform(self, type_env):
        #TODO: Extend the type env from var to type
        pass



