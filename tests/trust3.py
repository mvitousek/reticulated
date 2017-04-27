def f(x:Trusted[int])->Trusted[int]:
    return x

def g(x:int, y:Any):
    return f(y)
