def double(x:int)->int:
    return 2 * x
def funky(x:int)->Dyn:
    if x > 0: 
        return str(x)
    else: return 0 - x

@fields({'x':Function([int], Dyn)})
class C:
    def __init__(self):
        self.x = funky

c = C()

c.x = double

def f(obj:{'x':Function([Dyn], str)}):
    pass

f(c)
c.x(42)
