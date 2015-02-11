def g(x):
    x(10)

def f(x:Function([Dyn], Dyn)):
    g(x)

def k():
    pass

f(k)
