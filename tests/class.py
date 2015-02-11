from classimp import *

def makeinst(c:C.Class, x:int)->C:
    return c(x)

D = 20

makeinst(C, 30).x

makeinst(D, 30).x
