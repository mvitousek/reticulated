class D: 
    def f(self, x:int)->int:
        return x
    g = f

print(D().g('a'), __typeof(D().g('a')))
