def appint(fn: Function([int], int), x:int) -> int:
    return fn(x)

print(appint(lambda x: eval('20'), 10))
