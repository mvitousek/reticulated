from . import ctypes

class Constraint:
    def __repr__(self):
        return self.__str__()
    def subst(self, x, t):
        raise Exception()
    def vars(self):
        raise Exception()
    def solvable(self, v):
        raise Exception()

class STC(Constraint):
    def __init__(self, l, u):
        self.l = l
        self.u = u
    def __str__(self):
        return '{} <: {}'.format(self.l, self.u)
    def subst(self, x, t):
        return STC(self.l.subst(x,t), self.u.subst(x,t))
    def vars(self):
        return self.l.vars() + self.u.vars()
    def solvable(self, v):
        return v not in self.vars() or self.l is v

class InstanceSTC(Constraint):
    # Instance of the class on the left must be a subtype of type on the right
    def __init__(self, lc, u):
        self.lc = lc
        self.u = u
    def __str__(self):
        return 'Instance({}) <: {}'.format(self.lc, self.u)
    def subst(self, x, t):
        return InstanceSTC(self.lc.subst(x,t), self.u.subst(x,t))
    def vars(self):
        return self.lc.vars() + self.u.vars()
    def solvable(self, v):
        return v not in self.vars() or self.lu is v

class InhertitsC(Constraint):
    # Class on the right inherits from classes on the left
    def __init__(self, supers, cls):
        self.supers = supers
        self.cls = cls
    def __str__(self):
        return '{} extends {}'.format(self.cls, self.supers)


class EltSTC(Constraint):
    # Elements of the collection type on the left must be a subtype of type on the right
    def __init__(self, lc, u):
        self.lc = lc
        self.u = u
    def __str__(self):
        return 'Elements({}) <: {}'.format(self.lc, self.u)
    def subst(self, x, t):
        return EltSTC(self.lc.subst(x,t), self.u.subst(x,t))
    def vars(self):
        return self.lc.vars() + self.u.vars()
    def solvable(self, v):
        return v not in self.vars() or self.lu is v


class EqC(Constraint):
    def __init__(self, l, r):
        self.l = l
        self.r = r
    def __str__(self):
        return '{} = {}'.format(self.l, self.r)
    def subst(self, x, t):
        return EqC(self.l.subst(x,t), self.r.subst(x,t))
    def vars(self):
        return self.l.vars() + self.r.vars()
    def solvable(self, v):
        return v not in (self.l.vars() + self.r.vars())

class DefC(Constraint):
    def __init__(self, l, r):
        self.l = l
        self.r = r
    def __str__(self):
        return '{} := {}'.format(self.l, self.r)
    def subst(self, x, t):
        return DefC(self.l, self.r.subst(x,t))
    def vars(self):
        return self.l.vars() + self.r.vars()
    def solvable(self, v):
        return v not in self.l.vars() 

class BinopSTC(Constraint):
    def __init__(self, op, lo, ro, r):
        self.op = op
        self.lo = lo
        self.ro = ro
        self.r = r

class UnopSTC(Constraint):
    def __init__(self, op, lo, r):
        self.op = op
        self.lo = lo
        self.r = r

class CheckC(Constraint):
    def __init__(self, l, s, r):
        self.l = l
        self.s = s
        self.r = r
    def __str__(self):
        return '{}:{} = {}'.format(self.l, self.s, self.r)
    def subst(self, x, t):
        return CheckC(self.l.subst(x,t), self.s, self.r.subst(x,t))
    def vars(self):
        return self.l.vars() + self.r.vars()
    def solvable(self, v):
        return v not in self.r.vars()
