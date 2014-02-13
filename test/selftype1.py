class A:
    def f(self, other:Self):
        return other.g(self)
    def g(self, other:Self):
        return self.foo
    foo = 'bar'

class B(A):
    def g(self, other:Self):
        return other.baz
    baz = 'blah'

a = A()
b = B()

a.f(b)
