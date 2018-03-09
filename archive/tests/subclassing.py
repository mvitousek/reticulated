
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

print('\n\n\n\n\n')
print(m)
print(m, type(m))
print('\n\n\n\n\n')

d = m('a')

d.f(10)

class E:
    pass

class Quoter(E,C):
    pass

if True:
    o = Quoter
else: o = 43
