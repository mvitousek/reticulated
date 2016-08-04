class B:
    foo = 42
    def g(self, c:'C'):
        pass

class C:
    x = 1
    def f(self, x:int, y, z:'C', w:B)->int:
        w.g(y)
        return x + z.x

def f(x:C):
    x.f(10,20,x,B())

f(C())
