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

def fun(x:int)->int:
    return x

def app(x:Function([Dyn], Dyn), m:Dyn):
    x(m)

answer(app, fun, 10, ans=None)
error(app, fun, 'hi')

def fun2(x):
    return x

def fun3(x):
    return 'hi'

def fun4(x,y):
    return x

def fun5(x:str)->str:
    return x

def app2(x:Function([Int], Int), m:Int):
    x(m)

answer(app2, fun2, 10, ans=None)
error(app2, fun3, 10)
error(app2, fun4, 10)
error(app2, fun5, 10)

def ret(x)->int:
    return x

answer(ret, 10, ans=10)
error(ret, 'hi')

def r2(x)->int:
    if False:
        return 1
    else:
        return x

answer(r2, 7, ans=7)
error(r2, 'hi')

class C(object):
    a = 10

def deletion1(x:int, y:{'a':int}, z):
    del x
error(deletion1, 1, C(), 1)
 
def deletion2(x:int, y:{'a':int}, z):
    del y.a
error(deletion2, 1, C(), 1)

def deletion3(x:int, y:{'a':int}, z):
    del z
answer(deletion3, 1, C(), 1, ans=None)

def deletion4(x:int, y:{'a':int}, z):
    del y.b
k = C()
k.b = 15
answer(deletion4, 1, k, 1, ans=None)
error(deletion4, 1, k, 1)

def deletion4post(k):
    k.b
error(deletion4post, k)

def deletion5(x:int, y:{'a':int}, z):
    del y.c
error(deletion5, 1, k, 1)

def obj1(x:{'a':bool}):  
    x.a
error(obj1, C())

def obj2(x:{'a':int}):
    y = x
    y.a = 2j
    x.a
error(obj2, C())

def obj3(x:{'a':int}):
    x.a /= 4
error(obj3, C())

class D(object):
    a = 'hello'

def fortest(x:{'a':str}):
    for x.a in [1,'a',3]:
        pass
    else:
        x.a
error(fortest, D())

def fortest2(x:{'a':int}):
    for x.a in [1,2,3]:
        pass
    x.a
answer(fortest2, C(), ans=None)
