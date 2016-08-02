def f(x:Tuple[int, str, int])->Tuple[int, int]:
    return x[::2]

print(f((1,'a',3)))
