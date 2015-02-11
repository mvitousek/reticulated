def f(x:{'a' : int}):
    x.a

class M:
    a = 3

p = M()
print(p.__dict__)
f(p)
print(p.__dict__)
