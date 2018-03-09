def f(x:str):
    return x

class A:
    def f(self, x:{'x':int, 'z':int})->{'y':int}:
        return f(10)
class B:
    def f(self, x:{'x':int})->{'y':int, 'w':int}:
        return f(10)

def n(x):
    pass

if True:
    a = A()
else:
    a = B()

n(a)

