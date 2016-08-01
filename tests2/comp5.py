def pret(y, x):
    print(y)
    return x

def f(x:List[str])->List[Any]:
    return [x for x in pret(__typeof(x), x)]

f(['a'])[0]
