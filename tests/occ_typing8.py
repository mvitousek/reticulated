#test fails because x has type bool
def f(x:Union[str, bool]):
    if isinstance(x, bool):
        x1(x)
    else:
        pass

def x1(u:str):
    pass




f("3")
f(True)