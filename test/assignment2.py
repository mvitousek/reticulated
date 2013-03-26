from testing import *

@retic_typed(Function([int, str], Dyn))
def is_(i, s):
    m = s
    i = m
error(is_, 10, 'hi')

@retic_typed(Function([bool, int, float, complex, str], Dyn))
def augbbb(b, i, f, c, s):
    b = b + b
error(augbbb, True, 1, 1.5, 2j, "3")

@retic_typed(Function([bool, int, float, complex, str], Dyn))
def augibb(b, i, f, c, s):
    i = b + b
answer(augibb, True, 1, 1.5, 2j, "3", ans=None)

@retic_typed(Function([bool, int, float, complex, str], Dyn))
def augiib(b, i, f, c, s):
    i = i + b
    i = b + i
answer(augiib, True, 1, 1.5, 2j, "3", ans=None)

@retic_typed(Function([bool, int, float, complex, str], Dyn))
def augbib(b, i, f, c, s):
    b = i + b
error(augbib, True, 1, 1.5, 2j, "3")

@retic_typed(Function([bool, int, float, complex, str], Dyn))
def augbbbl(b, i, f, c, s):
    b = b | b
answer(augbbbl, True, 1, 1.5, 2j, "3", ans=None)

@retic_typed(Function([bool, int, float, complex, str], Dyn))
def augmc(b, i, f, c, s):
    2j % 4
error(augmc, True, 1, 1.5, 2j, "3")

@retic_typed(Function([bool, int, float, complex, str], Dyn))
def augbtx(b, i, f, c, s):
    b = b * (1,)
error(augbtx, True, 1, 1.5, 2j, "3")

@retic_typed(Function([int], Dyn))
def lista1(x):
    [x, y] = [1,2]
answer(lista1,10, ans=None)

@retic_typed(Function([int], Dyn))
def lista2(x):
    [x, y] = ['a',2]
error(lista2,10)

@retic_typed(Function([List(int)], Dyn))
def lista3(x):
    [x, y] = [[1,2],[2]]
answer(lista3,[10],ans=None)

def lista4():
    [x, y] = [5,[2]]
answer(lista4, ans=None)

def lista5():
    [x, y] = (5,2)
answer(lista5, ans=None)

@retic_typed(Function([int], Dyn))
def tupa1(x):
    (x, y) = (1,2)
answer(tupa1,10, ans=None)

@retic_typed(Function([int], Dyn))
def tupa2(x):
    (x, y) = ('a',2)
error(tupa2,10)

@retic_typed(Function([List(int)], Dyn))
def tupa3(x):
    (x, y) = ([1,2],[2])
answer(tupa3,[10],ans=None)

def tupa4():
    (x, y) = (5,[2])
answer(tupa4, ans=None)

def tupa5():
    (x, y) = [5,2]
answer(tupa5, ans=None)
