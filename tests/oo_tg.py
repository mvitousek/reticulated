class C:
    def __init__(self):
        self.x = 10

c = C()
def f(x:{'x':Dyn}):
    print(type(x))
    x.x = "hello"

def g(x:{'x':Int}):
    f(x)

g(c)
