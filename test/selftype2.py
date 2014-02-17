class A:
    def f(self:Self, other:Self):
        return other.g(self)
    def g(self:Self, other:Self):
        return self.foo
    foo = 'bar'

class B:
    def f(self:Self, other:Self):
        return other.g(self)
    def g(self, other:Self):
        return other.baz
    baz = 'blah'

A().f(B())
