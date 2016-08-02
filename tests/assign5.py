def f(x:int):
    if True:
        y = 42
    else:
        y = 'a'
    print(__typeof(y))

f(42)
