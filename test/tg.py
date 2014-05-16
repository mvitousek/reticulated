class C:
    pass
c = C()
c.x = 10

def f(x):
    x.x = "hello"
def g(x:{'x':Int})->int:
    f(x)
    return x.x
g(c)
