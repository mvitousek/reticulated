def f(x:Tuple[int, str, int])->int:
    print(__typeof(x[0:2]))
    return x[0]

f((1,'a',3))
