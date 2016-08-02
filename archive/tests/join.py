class A:
    def f(self, x:{'x':Int, 'z':Int})->{'y':Int}:
        return dyn(10)
class B:
    def f(self, x:{'x':Int})->{'y':Int, 'w':Int}:
        return dyn(10)

def n(x):
    pass

if True:
    a = A()
else:
    a = B()

n(a)

