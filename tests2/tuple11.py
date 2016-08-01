def f(x:Tuple[int, str, str])->Tuple[int, int]:
    return x[::2]

print(f((1,'a','v')))
