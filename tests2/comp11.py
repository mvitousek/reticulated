
def f(x:List[List[str]])->List[Any]:
    return [x for x in x for y in x]

def g(x): f(x)

g(['a'])[0]
