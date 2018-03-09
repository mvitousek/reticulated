def g(x):
    x(10)

def f(x:Function(..., Any)):
    g(x)

def k():
    pass

f(k)
