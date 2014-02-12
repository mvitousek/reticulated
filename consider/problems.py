# The type of tuple elements cannot be statically known, resulting in a Dyn=>T cast on something that is not injected, potentially:
def f(x:int, y:Tuple(bool, int))->int:
    return y[x]
