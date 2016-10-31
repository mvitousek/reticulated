def f(x:Union[int, str]):
    if isinstance(x, str):
        s1(x)
    else:
        s2(x)

def s1(a:str):
    pass

def s2(a:int):
    pass


f(10)
f("Hello World")