from testing import *

def is_(i:int, s:str):
    m = s
    i = m
error(is_, 10, 'hi')

def augbbb(b:bool, i:int, f:float, c:complex, s:str):
    b = b + b
error(augbbb, True, 1, 1.5, 2j, "3")

def augibb(b:bool, i:int, f:float, c:complex, s:str):
    i = b + b
answer(augibb, True, 1, 1.5, 2j, "3", ans=None)

def augiib(b:bool, i:int, f:float, c:complex, s:str):
    i = i + b
    i = b + i
answer(augiib, True, 1, 1.5, 2j, "3", ans=None)

def augbib(b:bool, i:int, f:float, c:complex, s:str):
    b = i + b
error(augbib, True, 1, 1.5, 2j, "3")

def augbbbl(b:bool, i:int, f:float, c:complex, s:str):
    b = b | b
answer(augbbbl, True, 1, 1.5, 2j, "3", ans=None)

def augmc(b:bool, i:int, f:float, c:complex, s:str):
    2j % 4
error(augmc, True, 1, 1.5, 2j, "3")

def augbtx(b:bool, i:int, f:float, c:complex, s:str):
    b = b * (1,)
error(augbtx, True, 1, 1.5, 2j, "3")

def lista1(x:int):
    [x, y] = [1,2]
answer(lista1,10, ans=None)

def lista2(x:int):
    [x, y] = ['a',2]
error(lista2,10)

def lista3(x:List(int)):
    [x, y] = [[1,2],[2]]
answer(lista3,[10],ans=None)

def lista4():
    [x, y] = [5,[2]]
answer(lista4, ans=None)

def lista5():
    [x, y] = (5,2)
answer(lista5, ans=None)

def tupa1(x:int):
    (x, y) = (1,2)
answer(tupa1,10, ans=None)

def tupa2(x:int):
    (x, y) = ('a',2)
error(tupa2,10)

def tupa3(x:List(int)):
    (x, y) = ([1,2],[2])
answer(tupa3,[10],ans=None)

def tupa4():
    (x, y) = (5,[2])
answer(tupa4, ans=None)

def tupa5():
    (x, y) = [5,2]
answer(tupa5, ans=None)

