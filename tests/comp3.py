def f(x:List[str])->List[Any]:
    return [print(__typeof(x)) for x in x]

f(['a'])[0]
