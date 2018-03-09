def f(x:int, y:str, w):
    [x, y] = *w

f(1,'a',['a',1])
