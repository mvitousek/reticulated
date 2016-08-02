
def f(x:List[Tuple[int,str]])->List[str]:
    return [a * b for a, b in x]

def g(x):
    f(x)

g([('a', 10)])[0]
