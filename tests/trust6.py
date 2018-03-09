def f(x:Callable[[int], int], z:int)->int:
    return x(z)

@positional
def g(x:int)->int:
    return x

f(g, 10)
