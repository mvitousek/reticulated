#implement warning
def f(x:Union[int, str]):
    if isinstance(x, bool):
        sfun(x)
    else:
        pass

def sfun(a:bool):
    pass

