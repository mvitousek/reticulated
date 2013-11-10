def f(x:{'a' : Int}):
    x.a
    x.a
    
class M:
    a = 3

p = M()
f(p)
p.a = 99
