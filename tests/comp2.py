def f(x:int)->List[Any]:
    return [print(__typeof(x)) for x in ['a']]

f(10)[0]
