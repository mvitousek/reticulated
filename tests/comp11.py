
def f(x:List[List[str]])->List[Any]:
    return [1 for x in x for y in x]

def g(x): f(x)

g(['a'])[0]
