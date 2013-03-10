from testing import *

def is_(x:int)->int:
    return x
answer(is_, 10, ans=10)

def i(x:int)->int:
    z = x
    return z
answer(i, 10, ans=10)
error(i, 'hi')

def c(x:complex)->complex:
    z = x
    return z
answer(c, 2j, ans=2j)
error(c, 1.5)

def f(x:float)->float:
    z = x
    return z
answer(f, 2.2, ans=2.2)
error(f, 2j)

def b(x:bool)->bool:
    z = x
    return z
answer(b, True, ans=True)
error(b, 2)

def t(x:Tuple(int,int))->Tuple(int,int):
    z = x
    return z
answer(t, (2,4), ans=(2,4))
error(t, (2.3, 1.2))

def l(x: List(int))->List(int):
    z = x
    return x
answer(l, [1,2], ans=[1,2])
error(l, [1,3.4])

def s(x: str)->str:
    z = x
    return x
answer(s, 'hi', ans='hi')
error(s, [])

def if_(x:int)->int:
    z = 'hello'
    return z
error(if_, 10)

def cf(x:complex)->complex:
    z = 'hello'
    return z
error(cf, 1.2j)

def ff(x:float)->float:
    z = 'hi'
    return z
error(ff, 1.5)

def bf(x:bool)->bool:
    z = 2
    return z
error(bf, True)

def tf(x:Tuple(int,int))->Tuple(int,int):
    z = 2
    return z
error(tf, (1,2))

def lf(x: List(int))->List(int):
    z = 2
    return z
error(lf, [1,2,3])

def sf(x: str)->str:
    z = 2
    return z
error(sf, 'hi')
