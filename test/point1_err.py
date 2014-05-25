class Point:
   def __init__(self):
       self.x = 0

   def equal(self:Point, o : {'x':int,'equal':int}) -> bool:
       return self.x == o.x

def f(x : int):
    pass

p = Point() # Obj(Point){'equal': Function(["o:Obj(){'x': Int}"], Bool)}
q = Point()
b = p.equal(q) # type error
print(b)

