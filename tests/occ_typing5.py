#implement warning
def f(x:Union[int, str, bool]):
    if isinstance(x, bool):
        return sbool(x)
    elif isinstance(x, str):
        return sstr(x)
    else:
        return sint(x)

def sbool(a:bool):
    pass

def sint(a:int):
    pass

def sstr(a:str):
    pass


f("Hello world")
f(True)
f(3)

