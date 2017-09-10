from . import ctypes

class Constraint:
    def __repr__(self):
        return self.__str__()
    def __str__(self):
        raise Exception(type(self))
    def __eq__(self, other):
        raise Exception(type(self))
    def subst(self, x, t):
        raise Exception()
    def vars(self, ctbl):
        raise Exception()
    def solvable(self, v, deps, ctbl):
        raise Exception()
    def __hash__(self):
        raise Exception()

class STC(Constraint):
    def __init__(self, l, u):
        self.l = l
        self.u = u
    def __str__(self):
        return '{} <: {}'.format(self.l, self.u)
    def __eq__(self, other):
        return isinstance(other, STC) and other.l == self.l and other.u == self.u
    def __hash__(self):
        return hash(self.l) + hash(self.u)
    def subst(self, x, t):
        return STC(self.l.subst(x,t), self.u.subst(x,t))
    def vars(self, ctbl):
        return self.l.vars(ctbl) + self.u.vars(ctbl)
    def solvable(self, v, deps, ctbl):
        return (v not in self.vars(ctbl) and v not in deps) or self.l is v

class InstanceSTC(Constraint):
    # Instance of the class on the left must be a subtype of type on the right
    def __init__(self, lc, u):
        self.lc = lc
        self.u = u
    def __str__(self):
        return 'Instance({}) <: {}'.format(self.lc, self.u)
    def __eq__(self, other):
        return isinstance(other, InstanceSTC) and other.lc == self.lc and other.u == self.u
    def __hash__(self):
        return hash(self.lc) + hash(self.u)
    def subst(self, x, t):
        return InstanceSTC(self.lc.subst(x,t), self.u.subst(x,t))
    def vars(self, ctbl):
        return self.lc.vars(ctbl) + self.u.vars(ctbl)
    def solvable(self, v, deps, ctbl):
        return v not in self.vars(ctbl) or self.u is v

class InheritsC(Constraint):
    # Classname on the right inherits from classes on the left
    def __init__(self, supers, cls):
        self.supers = supers
        self.cls = cls
    def __str__(self):
        return '{} extends {}'.format(self.cls, self.supers)
    def __hash__(self):
        return sum([hash(sup) for sup in self.supers], 0) + hash(self.cls)
    def __eq__(self, other):
        return isinstance(other, InheritsC) and other.supers == self.supers and other.cls == self.cls
    def vars(self, ctbl):
        return sum([k.vars(ctbl) for k in self.supers], [])
    def solvable(self, v, deps, ctbl):
        return True
    def subst(self, x, t):
        return InheritsC([k.subst(x,t) for k in self.supers], self.cls)


class EltSTC(Constraint):
    # Elements of the collection type on the left must be a subtype of type on the right
    def __init__(self, lc, u):
        self.lc = lc
        self.u = u
    def __str__(self):
        return 'Elements({}) <: {}'.format(self.lc, self.u)
    def __eq__(self, other):
        return isinstance(other, EltSTC) and other.lc == self.lc and other.u == self.u
    def __hash__(self):
        return hash(self.lc) + hash(self.u)
    def subst(self, x, t):
        return EltSTC(self.lc.subst(x,t), self.u.subst(x,t))
    def vars(self, ctbl):
        return self.lc.vars(ctbl) + self.u.vars(ctbl)
    def solvable(self, v, deps, ctbl):
        return v not in self.vars(ctbl) or self.lc is v


class EqC(Constraint):
    def __init__(self, l, r):
        self.l = l
        self.r = r
    def __str__(self):
        return '{} = {}'.format(self.l, self.r)
    def __eq__(self, other):
        return isinstance(other, EqC) and other.l == self.l and other.r == self.r
    def __hash__(self):
        return hash(self.l) + hash(self.r)
    def subst(self, x, t):
        return EqC(self.l.subst(x,t), self.r.subst(x,t))
    def vars(self, ctbl):
        return self.l.vars(ctbl) + self.r.vars(ctbl)
    def solvable(self, v, deps, ctbl):
        return v not in (self.l.vars(ctbl) + self.r.vars(ctbl))



class BoundEqC(Constraint):
    def __init__(self, l, r):
        self.l = l
        self.r = r
    def __str__(self):
        return '{} = bind({})'.format(self.l, self.r)
    def __eq__(self, other):
        return isinstance(other, BoundEqC) and other.l == self.l and other.r == self.r
    def __hash__(self):
        return hash(self.l) + hash(self.r)
    def subst(self, x, t):
        return BoundEqC(self.l.subst(x,t), self.r.subst(x,t))
    def vars(self, ctbl):
        return self.l.vars(ctbl) + self.r.vars(ctbl)
    def solvable(self, v, deps, ctbl):
        return v not in (self.l.vars(ctbl) + self.r.vars(ctbl))
    
class DefC(Constraint):
    def __init__(self, l, r):
        self.l = l
        self.r = r
    def __str__(self):
        return '{} := {}'.format(self.l, self.r)
    def __hash__(self):
        return hash(self.l) + hash(self.r)
    def __eq__(self, other):
        return isinstance(other, DefC) and other.l == self.l and other.r == self.r
    def subst(self, x, t):
        return DefC(self.l, self.r.subst(x,t))
    def vars(self, ctbl):
        return self.l.vars(ctbl) + self.r.vars(ctbl)
    def solvable(self, v, deps, ctbl):
        return v not in self.l.vars(ctbl) 

class BinopSTC(Constraint):
    def __init__(self, op, lo, ro, u):
        self.op = op
        self.lo = lo
        self.ro = ro
        self.u = u
    def __str__(self):
        return '{}{}{} <: {}'.format(self.lo, self.op, self.ro, self.u)
    def __eq__(self, other):
        return isinstance(other, BinopSTC) and other.op == self.op and other.lo == self.lo and other.ro == self.ro and other.u == self.u
    def __hash__(self):
        return hash(self.op) + hash(self.lo) + hash(self.ro) + hash(self.u)
    def subst(self, x, t):
        return BinopSTC(self.op, self.lo.subst(x,t), self.ro.subst(x,t), self.u.subst(x,t))
    def vars(self, ctbl):
        return self.lo.vars(ctbl) + self.ro.vars(ctbl) + self.u.vars(ctbl)
    def solvable(self, v, deps, ctbl):
        return v not in self.u.vars(ctbl)

class UnopSTC(Constraint):
    def __init__(self, op, lo, u):
        self.op = op
        self.lo = lo
        self.u = u
    def __str__(self):
        return '{}{} <: {}'.format(self.op, self.lo, self.u)
    def __eq__(self, other):
        return isinstance(other, UnopSTC) and other.op == self.op and other.lo == self.lo and other.u == self.u
    def __hash__(self):
        return hash(self.op) + hash(self.lo) + hash(self.u)
    def subst(self, x, t):
        return UnopSTC(self.op, self.lo.subst(x,t), self.u.subst(x,t))
    def vars(self, ctbl):
        return self.lo.vars(ctbl) + self.u.vars(ctbl)
    def solvable(self, v, deps, ctbl):
        return v not in self.u.vars(ctbl)

class CheckC(Constraint):
    def __init__(self, l, s, r):
        self.l = l
        self.s = s
        self.r = r
    def __str__(self):
        return '{}:{} = {}'.format(self.l, self.s, self.r)
    def __eq__(self, other):
        return isinstance(other, CheckC) and other.l == self.l and other.s == self.s and other.r == self.r
    def __hash__(self):
        return hash(self.l) + hash(self.r)
    def subst(self, x, t):
        return CheckC(self.l.subst(x,t), self.s, self.r.subst(x,t))
    def vars(self, ctbl):
        return self.l.vars(ctbl) + self.r.vars(ctbl)
    def solvable(self, v, deps, ctbl):
        return v not in self.r.vars(ctbl) and v not in deps

def depends(var, constraints, ctbl):
    assert isinstance(var, ctypes.CVar)
    deps = {var}
    odeps = {}
    while deps != odeps:
        odeps = deps
        for c in constraints:
            if isinstance(c, STC) and c.u in deps:
                deps |= set(c.l.vars(ctbl))
            elif isinstance(c, CheckC) and any(dep in c.r.vars(ctbl) for dep in deps):
                deps |= set(c.l.vars(ctbl))
    return deps
