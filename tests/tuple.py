def f(x:Tuple[int, int, int])->int:
    print(__typeof(x[1]))
    return x[0]

f((1,2,3))
