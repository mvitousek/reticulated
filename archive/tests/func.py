def f(x:str)->str:
    return x

def m(g:Function([Function([int], int)], Any), h:Any):
    g(h)

def o(a:Function([int], int)):
    a(10)

m(o, f)
