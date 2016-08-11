from imp4 import *

def f(k:C, x)->int:
    return k.x(x)

class D:
    def x()->str:
        return 'a'

f(D(), 20)
