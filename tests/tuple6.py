def f(x:Tuple[int, int, int], u)->int:
    print(__typeof(x[u:2][0]))
    return x[0]

f((1,4,3), 0)
