def f(x:Callable[[int], int], z:int)->int:
    return x(z)

@positional
def g(x:int)->int:
    return x

@positional
def h(x:Any)->Any:
    return 'a' 

f(h, 10)
