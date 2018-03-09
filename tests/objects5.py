def f(x:{'a' : int}):
    x.a

class M:
    a = 3

p = M()
q = M()
f(p)
q.a = 'hello'
