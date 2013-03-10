from testing import *

def is_(i:int, s:str):
    m = s
    i = m
error(is_, 10, 'hi')

def aug(b:bool, i:int, f:float, c:complex, s:str):
    s + b
    s += b
error(aug, True, 1, 1.5, 2j, "3")
