#x should have str type in the if clause
# y should have bool type so test should pass
def f(x:Union[str, bool], y:Union[str, bool]):
    if isinstance(x, str):
        if isinstance(y, bool):
            x1(x)
            y1(y)

    else:
        #~test?
        y1(x)


def x1(u:str):
    pass

def y1(v:bool):
    pass



f("a", "3")
f("a", True)
f(True, True)
f(True, "3")