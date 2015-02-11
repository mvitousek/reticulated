def f(x)->int:
    y = 3
    y = 60
    return y

def f(x)->int:
    if True:
        y = 3
    else:
        y = 60
    return y

def f(x)->int:
    if x:
        y = 3
    else:
        y = 'hello world'
    return y

def f(x)->int:
    if False:
        y = 3
    return y

def g(x)->int:
    x = 0
    for a in [1,2,3]:
        x = a
    return x

def g(x)->int:
    x = 0
    for a in [1,2,3]:
        x = x
    return x

def h(x) -> int:
    x = 0
    for a in [1,2,3]:
        if a > 1:
            x = y
            y = z
        z = x
    return z


def z(a):
    x = (42, a)
    x = (a, 41)
    return x

def z(a):
    x = (42, 42)
    x = (a, 42)
    return x

def i(a)->bool:
    x = (42, a)
    x = (a, 41)
    return x[0]

def b(x:bool):
    pass
