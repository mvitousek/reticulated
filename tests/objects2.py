
def f(x:{'a' : int}):
    x.a = 30
    
class M:
    a = 3

p = M()
f(p)
p.a = 30
p.a = 'hi'
