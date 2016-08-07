def f(x:{'a':int})->int: 
    return x.a

class C:
    a = 42

f(C())
