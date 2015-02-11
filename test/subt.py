
if True:
    x = [1,2,3]
else: x = ['a', 'b', 'c']

def f(y:List(Int)):
    y[0] = 5
    return y + x

print(f(x))

class M:
    def k(self, x:int)->int:
        return x

class N:
    def k(self, x):
        pass

def g(x:int)->int:
    return x + x

m = M()
m.k = g
print(m.k(50))

class P(list):
    def getitem(self, x:int)->int:
        return self[x]
    def setitem(self, x:int, y:int)->Void:
        self[x] = y
class G(list):
    def getitem(self, x:int):
        return self[x]
    def setitem(self, x:int, y)->Void:
        self[x] = y


if True:
    s = P([1,2,3])
else: s = G(['a', 'b', 'c'])

def e(y:{'setitem':Function([Int, Int], Void)}):
    y.setitem(0,5)
    return y + s

print(e(s))
