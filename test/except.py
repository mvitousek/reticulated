def f(x:int):
    print(x)
    try:
        raise Exception('aa')
    except Exception as x:
        print(repr(x))
    print(x)

f(10)
