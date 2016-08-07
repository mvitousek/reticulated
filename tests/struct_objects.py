def f(x:{'a' : int}):
    x.a
    
class M:
    a = 3
    def __str__(self:'M')->str:
        return 'a'


p = M()
print(p)
f(p)
p.a = 30
