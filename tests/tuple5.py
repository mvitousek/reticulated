def f(x:Tuple[int, str, int], u)->int:
    print(__typeof(x[u:2]))
    return x[0]

f((1,'a',3), 0)
