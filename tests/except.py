def f(x:int):
    print(reflect_type(x))
    try:
       raise Exception('aa')
    except Exception as x:
        print(reflect_type(x))
        print(repr(x))

f(10)

