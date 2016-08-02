
def f(x:List[str])->List[Any]:
    [x for x in x]
    print(__typeof(x))
    return [1]

f(['a'])[0]
