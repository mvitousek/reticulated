def f(x:str):
    print(x)

def g(x):
    if isinstance(x, int):
        return f(x)

