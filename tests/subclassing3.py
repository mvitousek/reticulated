
print('hoho')
class C:
    def __init__(self, y):
        pass
    def f(self, x:int)->int:
        return x

C('1')

if True:
    m = C
else: m = 20


d = m('a')

d.f(10)

class E:
    pass

class Quoter(E,C):
    pass

Quoter(42)
