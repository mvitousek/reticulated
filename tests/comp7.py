
def f(x:List[str])->List[Any]:
    return [x for x in x]

def g(x):
    f(x)

g([1])
