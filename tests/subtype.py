class A:
    def f(self, k:int)->int:
        return k

class B(A):
    def g(self, k:int)->int:
        return k

def cf(x:A, a:int)->int:
    return x.f(a)

print(cf(A(), 40), cf(B(), 40))
