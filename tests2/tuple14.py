def f(x:Tuple[int, str, str], u:int):
    a,b,c = x
    print(__typeof(c))

f((1,'a', 'a'),4)
