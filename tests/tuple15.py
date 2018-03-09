def f(x:Tuple[int, str, str], u:int)->Tuple[int, ...]:
    return x[::u]

f((1,'a','v'), 2)[1]
