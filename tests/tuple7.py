def f(x:Tuple[int, int, int], u)->int:
    print(__typeof(x[5]))
    return x[0]

f((1,4,3), 0)
