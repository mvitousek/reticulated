from __future__ import print_function
Self = "i am a type"
class Incorrect(Exception): pass

class A(object):
    def f(self:Self, other:Self):
        return other.g(self)
    def g(self:Self, other:Self):
        return self.foo
    def f_fixed(self:Self, other:Self):
        return self.__class__.g(other, self)
    foo = 'bar'

class B(A):
    def g(self:Self, other:Self):
        return other.name
    name = 'B'

a = A()
b = B()

try:
    a.f(b)
    raise Incorrect()
except AttributeError:
    pass

a.f_fixed(b)

######################################

class C(B):
    def g(self:Self, other:Self):
        return other.message
    message = 'Hello'

c = C()

try:
    b.f(c)
    raise Incorrect()
except AttributeError:
    pass

b.f_fixed(c)

######################################

class M(object): # Obj(Self) {f,f_fixed,g : Self x Self -> *, foo : str}
    def f(self:Self, other:Self):
        return other.g(self)
    def g(self:Self, other:Self):
        return self.foo
    def f_fixed(self:Self, other:Self):
        return self.__class__.g(other, self)
    foo = 'bar'

class N(object): # Obj(Self) {f,f_fixed,g : Self x Self -> *, foo,name : str}
    def f(self:Self, other:Self):
        return other.g(self)
    def g(self:Self, other:Self):
        return other.name
    def f_fixed(self:Self, other:Self):
        return self.__class__.g(other, self)
    foo = 'bar'
    name = 'B'

m = M()
n = N()

try:
    m.f(n)
    raise Incorrect()
except AttributeError:
    pass

m.f_fixed(n) # This works, but is weird. M's version of g is 
             # being invoked with an N instance as a receiver, 
             # even though N instances are not M instances.
             # This will NOT work in Python 2.X
