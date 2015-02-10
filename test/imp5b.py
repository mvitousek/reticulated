from imp4b import *

def f(k:C, x)->int:
    return k.x(x)

class D:
    def x()->str:
        return 'a'

print(reflect_subcompat(D(), C()))

f(D(), 20)
