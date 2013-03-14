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
