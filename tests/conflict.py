
def f(x:int)->int:
    return 42

def f(x:str)->str:
    return 'a'

def g(x:Function([int], int)):
    x(20)

print(__typeof(f))
print(g(f))
