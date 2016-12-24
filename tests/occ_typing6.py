def f(x:Union[str, bool], y:Union[str, bool]):
    if isinstance(x, bool) and isinstance(y, str):
        x1(x)
        y1(y)
    else:
        z1(x)
        z1(y)


def x1(x:bool):
    pass


def y1(x:str):
    pass


def z1(x:Union[str, bool]):
    pass


f("a", "3")
f("a", True)
f(True, True)
f(True, "3")