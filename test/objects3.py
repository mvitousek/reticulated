def f(x:{'a' : Int}):
    x.a
    
class M(metaclass=Monotonic):
    a = 3

p = M()
f(p)
M.a = 'hi'

