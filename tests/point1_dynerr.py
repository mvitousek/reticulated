class Point:
   x = 0
   def __init__(self):
       self.x = 0

   def equal(self:'Point', o : {'x':int,'equal':int}) -> bool:
       return o.x == self.x

def f(x):
    return x

p = Point() # Obj(Point){'equal': Function(["o:Obj(){'x': Int}"], Bool)}
q = Point()


b = p.equal(f(q)) # type error
print(b)

### THIS SHOULD BE A RUNTIME ERROR, SORT OF -- LOOK @ THE TYPES SUCKA
