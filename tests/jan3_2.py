@fields({'z':Dyn})
class A:
    def __init__(self):
        self.z = 'hello'

@fields({'z':int})
class B:
    def __init__(self):
        self.z = 21

@fields({'x':A})
class C:
    def __init__(self):
        self.x = A()

c = C()
a = c.x
a.z = 42

def f(obj:{'x':A}):
    obj.x = A()

f(c)
a.z = 'world'
