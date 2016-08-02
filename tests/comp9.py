
def f(x:List[List[str]])->List[Any]:
    return [print(__typeof(y)) for x in x for y in x]

f([['a']])[0]
