def f(x:{'a' : int}):
    x.a

class M:
    a = 3

p = M()
f(p)
