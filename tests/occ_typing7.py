def f(x:Union[str, bool], y:Union[str, bool]):
    if isinstance(x, bool) or isinstance(y, str):
        z1(x)
        z1(y)
    else:
        x1(x)
        y1(y)


def z1(g:Union[str, bool]):
    pass


def x1(u:str):
    pass

def y1(v:bool):
    pass


f("a", "3")
f("a", True)
f(True, True)
f(True, "3")