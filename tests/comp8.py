
def f(x:List[List[str]])->List[str]:
    return [y for x in x for y in x]

f([['a']])[0]
