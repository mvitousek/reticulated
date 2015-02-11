
def f(x:float)->int:
    return 42

def f(x:str)->str:
    return 'a'

def g(x:Function([float], int)):
    pass

print(reflect_type(f))

print(g(f))
