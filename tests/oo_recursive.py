@fields({'a':int})
class C:
    def __init__(self):
        self.a = 42
    def f(self, x:'C'):
        return x.a

def f(x:C):
    x.f(x)

f(C())

print(__typeof(C()))
