members = {}

class FlowVariableID: pass

class Root(FlowVariableID):
    def __init__(self, var:int):
        self.var = var
    def __str__(self):
        return 'v'+str(self.var)
    def __eq__(self, other):
        return isinstance(other, Root) and self.var == other.var
    def __hash__(self):
        return hash(self.var)
    __repr__ = __str__

class PosArgVar(FlowVariableID):
    def __init__(self, var:FlowVariableID, n:int):
        self.var = var
        self.n = n
    def __str__(self):
        return '?({}){}'.format(self.n, self.var)
    def __eq__(self, other):
        return isinstance(other, PosArgVar) and self.var == other.var \
            and self.n == other.n
    def __hash__(self):
        return hash(self.var) ^ hash(self.n)
    __repr__ = __str__

class RetVar(FlowVariableID):
    def __init__(self, var:FlowVariableID):
        self.var = var
    def __str__(self):
        return '!{}'.format(self.var)
    def __eq__(self, other):
        return isinstance(other, RetVar) and self.var == other.var
    def __hash__(self):
        return hash(self.var) ^ 99
    __repr__ = __str__

class ListEltVar(FlowVariableID):
    def __init__(self, var:FlowVariableID):
        self.var = var
    def __str__(self):
        return '[]{}'.format(self.var)
    def __eq__(self, other):
        return isinstance(other, ListEltVar) and self.var == other.var
    def __hash__(self):
        return hash(self.var) ^ 88
    __repr__ = __str__

class MemVar(FlowVariableID):
    def __init__(self, var, key):
        self.var = var
        self.key = key
        if var in members:
            members[var].append(self)
        else:
            members[var] = [self]
    def __str__(self):
        return '[.{}]{}'.format(self.key, self.var)
    def __eq__(self, other):
        return isinstance(other, MemVar) and self.var == other.var \
            and self.key == other.key
    def __hash__(self):
        return hash(self.var) ^ hash(self.key) ^ 99
    __repr__ = __str__
