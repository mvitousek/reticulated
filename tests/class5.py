class C: 
    pass

def f(x:C):
    print(__typeof(x))

f(C())
