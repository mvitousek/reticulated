from classimp import *

def makeinst(c:C.Class, x:int)->C:
    return c(x)

D = 20

makeinst(C, 30).x

print(reflect_type(makeinst), reflect_type(D))

makeinst(D, 30).x
