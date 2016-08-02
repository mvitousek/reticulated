from imp4 import *

def f(k:C, x)->int:
    return k.x(x)

f(C(), 20)

class D:
    pass

def g(c:D.Class)->D:
    return c()

g(D)
