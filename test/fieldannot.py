@fields({'x':int})
class C:
    x = 30

def f(x:int):
    pass

def g(x:{'x':int}):
    pass

f(C.x)
f(C().x)
g(C())
