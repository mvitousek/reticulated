def f(x:{'a' : Int}):
    x.a
    
class M:
    a = 3

p = M()
f(p)
M.a = 'hi'

