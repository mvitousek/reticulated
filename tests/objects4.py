def f(x:{'a' : int}):
    x.a
    
def g(x:{'a':Any}):
    x.a

class M:
    a = 3

p = M()
q = M()
g(q)
f(p)
q.a = 'hello'
