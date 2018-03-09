class C: 
    pass

def f(x:C):
    print(__typeof(x))

def g(x):
    f(x)

g(42)
