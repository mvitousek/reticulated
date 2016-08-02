def f(x:int):
    if True:
        def g(x:int): pass
    else:
        def g(x:str): pass
    print(__typeof(g))

f(42)
