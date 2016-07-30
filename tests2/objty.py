class B:
    foo = 42
    def g(self, c:C):
        pass

class C:
    x = 1
    def f(self, x:int, y, z:Self, w:B)->int:
        return x + z.x

def f(x:C):
    pass

def g(x:C.Class):
    pass

f(C())
