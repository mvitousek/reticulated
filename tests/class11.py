class D: 
    def f(self, x:int)->int:
        return x

class C(D):
    pass

print(C().f(10), __typeof(C().f(10)))
