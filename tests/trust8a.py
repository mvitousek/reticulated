def f(x:Callable[[int], int], z:int)->int:
    return x(z)

@positional
def g(x:int)->int:
    return x

@positional
def h(x:int)->Any:
    return 20

f(h, 10)
