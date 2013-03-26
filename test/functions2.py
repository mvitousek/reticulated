from testing import *

@retic_typed(Function([Int], Int))
def is_(x):
    return x
answer(is_, 10, ans=10)

@retic_typed(Function([Int], Int))
def i(x):
    z = x
    return z
answer(i, 10, ans=10)
error(i, 'hi')

@retic_typed(Function([Complex], Complex))
def c(x):
    z = x
    return z
answer(c, 2j, ans=2j)
error(c, 1.5)

@retic_typed(Function([Float], Float))
def f(x):
    z = x
    return z
answer(f, 2.2, ans=2.2)
error(f, 2j)

@retic_typed(Function([bool], bool))
def b(x):
    z = x
    return z
answer(b, True, ans=True)
error(b, 2)

@retic_typed(Function([Tuple(int,str)], Tuple(int,str)))
def t(x):
    z = x
    return z
answer(t, (2,'a'), ans=(2,'a'))
error(t, (2.3, 1.2))

@retic_typed(Function([List(Int)], List(int)))
def l(x):
    z = x
    return x
answer(l, [1,2], ans=[1,2])
error(l, [1,3.4])

@retic_typed(Function([str], str))
def s(x):
    z = x
    return x
answer(s, 'hi', ans='hi')
error(s, [])

@retic_typed(Function([int],int))
def if_(x):
    z = 'hello'
    return z
error(if_, 10)

@retic_typed(Function([complex],complex))
def cf(x):
    z = 'hello'
    return z
error(cf, 1.2j)

@retic_typed(Function([float],float))
def ff(x):
    z = 'hi'
    return z
error(ff, 1.5)

@retic_typed(Function([bool],bool))
def bf(x):
    z = 2
    return z
error(bf, True)

@retic_typed(Function([Tuple(int,int)],Tuple(int,int)))
def tf(x):
    z = 2
    return z
error(tf, (1,2))

@retic_typed(Function([List(int)],List(int)))
def lf(x):
    z = 2
    return z
error(lf, [1,2,3])

@retic_typed(Function([str],str))
def sf(x):
    z = 2
    return z
error(sf, 'hi')

@retic_typed(Function([int],int))
def fun(x):
    return x

@retic_typed(Function([Function([Dyn], Dyn), Dyn], Dyn))
def app(x, m):
    x(m)

answer(app, fun, 10, ans=None)
error(app, fun, 'hi')

def fun2(x):
    return x

def fun3(x):
    return 'hi'

def fun4(x,y):
    return x

@retic_typed(Function([str],str))
def fun5(x):
    return x

@retic_typed(Function([Function([int],int), Int], Dyn))
def app2(x, m):
    x(m)

answer(app2, fun2, 10, ans=None)
error(app2, fun3, 10)
error(app2, fun4, 10)
error(app2, fun5, 10)

@retic_typed(Function([Dyn],int))
def ret(x):
    return x

answer(ret, 10, ans=10)
error(ret, 'hi')

@retic_typed(Function([Dyn],int))
def r2(x):
    if False:
        return 1
    else:
        return x

answer(r2, 7, ans=7)
error(r2, 'hi')

class C(object):
    a = 10

@retic_typed(Function([Int, {'a':int}, Dyn],Dyn))
def deletion1(x, y, z):
    del x
error(deletion1, 1, C(), 1)
 
@retic_typed(Function([Int, {'a':int}, Dyn],Dyn))
def deletion2(x, y, z):
    del y.a
error(deletion2, 1, C(), 1)

@retic_typed(Function([Int, {'a':int}, Dyn],Dyn))
def deletion3(x, y, z):
    del z
answer(deletion3, 1, C(), 1, ans=None)

#ef deletion4(x:int, y:{'a':int}, z):
#    del y.b
#k = C()
#k.b = 15
#nswer(deletion4, 1, k, 1, ans=None)
#error(deletion4, 1, k, 1)

#def deletion4post(k):
#   k.b
#error(deletion4post, k)

#def deletion5(x:int, y:{'a':int}, z):
#    del y.c
#error(deletion5, 1, k, 1)

@retic_typed(Function([{'a':bool}],Dyn))
def obj1(x):  
    x.a
error(obj1, C())

@retic_typed(Function([{'a':int}],Dyn))
def obj2(x):
    y = x
    y.a = 2j
    x.a
error(obj2, C())

@retic_typed(Function([{'a':int}],Dyn))
def obj3(x):
    x.a /= 4
error(obj3, C())

class D(object):
    a = 'hello'

@retic_typed(Function([{'a':str}],Dyn))
def fortest(x):
    for x.a in [1,'a',3]:
        pass
    else:
        x.a
error(fortest, D())

@retic_typed(Function([{'a':int}],Dyn))
def fortest2(x):
    for x.a in [1,2,3]:
        pass
    x.a
answer(fortest2, C(), ans=None)

# Statically rejected
#def while1()->int:
#    while True:
#        return 10
#error(while1)

@retic_typed(Function([],int))
def while2():
    while True:
        return 10
    else:
        return 10
answer(while2, ans=10)

# Statically detected
#def while3()->int:
#    while True:
#        break
#        return 10
#    else:
#        return 10
#error(while3)

@retic_typed(Function([{'a':int}],Dyn))
def gentest(x):
    return [x for x.a in ['a', 'b', 2]]
error(gentest, C())

@retic_typed(Function([int], Function([str], int)))
def outer(x):
    @retic_typed(Function([str], Dyn))
    def inner(x):
        return 4
    return inner
fkk = outer(20)('a')
