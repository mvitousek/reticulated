def f(x:Trusted[int])->Trusted[int]:
    return x

def g(x:int):
    return f(10)
