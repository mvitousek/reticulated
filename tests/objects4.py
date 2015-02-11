def f(x:{'a' : Int}):
    x.a
    
def g(x:{'a':Dyn}):
    x.a

class M:
    a = 3

p = M()
q = M()
g(q)
f(p)
q.a = 'hello'
