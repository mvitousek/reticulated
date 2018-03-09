@fields({'a':bool})
class C:
    def f(self, x:int)->bool:
        return True

def h(g:C):
    g.f(10)

h(C())
