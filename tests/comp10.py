
def f(x:List[str], y:List[int])->List[Any]:
    return [x + y for x in x for y in y]

f(['a'],[9])[0]
