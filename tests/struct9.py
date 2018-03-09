def f(x:{'a':int})->int: 
    return x.a

def g(x:{}):
    f(x)

class D:
    a = 42
    b = 'a'

g(D())
