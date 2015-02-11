def f(x:int, y:str, foo:List(Dyn)):
    [x,y] = foo

f(1,'a', [1,'a'])
