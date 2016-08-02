def f(x:Tuple[int, int, int])->int:
    print(__typeof(x[1]))
    return x[1]

def g(x):
    f(x)

g((1,'a',3))
