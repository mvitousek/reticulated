def f(x:int):
    pass

def m(): pass

def g():
    f = m
    f()

g()
