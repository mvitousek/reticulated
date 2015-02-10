def f(x:str)->str:
    return x

def m(g:Function([Function([int], int)], Dyn), h:Dyn):
    g(h)

def o(a:Function([int], int)):
    a(10)

m(o, f)
