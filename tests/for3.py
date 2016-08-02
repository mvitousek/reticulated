def f(x:List[Any]):
    ss = 0
    for a in x:
        print(__typeof(ss + a))

f([1])
