
def f(x:float)->int:
    return 42

def f(x:str)->str:
    return 'a'

def g(x:Function([float], int)):
    pass

print(__typeof(f))

print(g(f))
