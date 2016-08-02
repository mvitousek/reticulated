@fields({'x':Dyn})
class C:
    #def __init__(self):
    #    self.x = 42
    x = 42



c = C()

print(c)

print(reflect_type(c))

c.x = 'hello'

def f(obj:{'x':str}):
    obj.x = 'world'

f(c)

c.x = 42
print(c.x)
