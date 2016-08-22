@fields({'z':Dyn})
class A:
    def __init__(self):
        self.z = 'hello'

@fields({'z':int})
class B:
    def __init__(self):
        self.z = 21

@fields({'x':{'z':Dyn}})
class C:
    def __init__(self):
        self.x = A()

c = C()
a = c.x
a.z = 42

def f(obj:{'x':{'z':int}}):
    obj.x = B()

f(c)
a.z = 'world'
