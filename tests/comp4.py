def f(x:List[str])->List[Any]:
    return [x for x in x if print(__typeof(x)) or True]

f(['a'])[0]
