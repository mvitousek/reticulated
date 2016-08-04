class D: 
    def f(self, x:int)->int:
        return x
    g = f

print(D().g(10), __typeof(D().g(10)))
