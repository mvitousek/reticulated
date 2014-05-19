def f(x:{'a' : Int}):
    x.a
    
class M:
    a = 3


p = M()
print(p)
f(p)
p.a = 30
