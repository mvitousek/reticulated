
class A:
    def f(self, other:A):
        return other.g(self)
    def g(self, other:A):
        return self.foo
    foo = 'bar'

class B(A):
    def g(self, other:B):
        return other.baz
    baz = 'blah'

print(A().f(B()))

