def f(x:Tuple[int, str, int])->int:
    print(__typeof(x[5:]))
    return x[5:][0]

f((1,'a',3))
