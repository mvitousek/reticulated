def f(x:int)->int:
    print(__typeof(x))
    return x

def g(x:Any):
    return f(x)

g(10)
