def f(x:float, l:List(float))->float:
    for i in l:
        x += i
    return x

f(10., [1.,2.,3.])
