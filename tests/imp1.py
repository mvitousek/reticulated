import imp2

def f(k:Callable[[int], int]):
    print(__typeof(imp2.x))
    k(imp2.x)

f(imp2.z)
