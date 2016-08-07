def f(x:{'a':int})->int: 
    return x.a

def g(x):
    f(x)

class D: pass

g(D())
