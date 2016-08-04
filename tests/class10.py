class D: 
    def f(self, x:int)->int:
        return x

print(D().f(10), __typeof(D().f(10)))
