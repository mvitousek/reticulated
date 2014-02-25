def a()->int:
    return 10

z = a()
y = 'a'

def x(a:int)->int:
    return z

class C:
    def a(self, p:int)->int:
        return p

x(C().a(10))
