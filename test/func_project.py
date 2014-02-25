a = [1,2,3]

def b(x:str)->int:
    return 20

def f(c, d:int):
    try:
        c(d)
        print('Callable')
    except TypeError:
        print('Noncallable')

f(b, 20)
