

class X:
    def f(self, x:'X', y:'Y', z:'Z'):
        pass
class Y:
    def f(self, x:X, y:'Y', z:'Z'):
        pass
class Z:
    def f(self, x:X, y:Y, z:'Z'):
        pass

def foo(x):
    return x

Z().f(X(),Y(),foo(Y()))
