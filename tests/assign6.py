def f(x:int):
    if True:
        def g(x:int): pass
    else:
        def g(x:int): pass

f(42)
