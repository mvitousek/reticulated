class A:
    def f(self, other:A):
        return 'a'

A().f(A())
