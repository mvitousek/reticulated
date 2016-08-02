@fields({'x':Any})
class C:
    def __init__(self):
        self.x = 42



c = C()

c.x = 'hello'

def f(obj:{'x':str}):
    obj.x = 'world'
f(c)
c.x = 42
