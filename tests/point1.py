class Point:
   x = -1
   def __init__(self):
       self.x = 0

   def equal(self:'Point', o : {'x':int}) -> bool:
       return self.x == o.x

def f(x : int):
    pass

p = Point() # Obj(Point){'equal': Function([Obj(){'x': Int}], Bool)}
q = Point() # ditto
b = p.equal(q) # q : Obj(Point){...} => Obj(){'x': Int}
print(b)

