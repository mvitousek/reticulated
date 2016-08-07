def f(x) -> (List(int), int):
    return x,x[1]

def dyn(x): return x

z = dyn([1,2])
z[0] = 4

m,n = f(z)

def g(x:int):
    print(x)

g(m[0])

class C:
    x = 40
class T:
    def __init__(self, x, y):
        self.x = x
        self.y = y
    x = 0
    y = 0
    def tself(self)->{'x':{'x':int}, 'y':int}:
        return self

def coerce(c)->({'x':int},int):
    return c, 10

def cf(x) -> {'x':{'x':int}, 'y':int}:
    return T(x,x.x).tself()

oz = C()
oz.x = 2.5

cz,_ = coerce(oz)

gr = cf(cz)
cm = gr.x
cn = gr.y

def cg(x:int):
    print(x)

cg(cm.x)
