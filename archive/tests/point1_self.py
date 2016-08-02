class Point:
   def __init__(self):
       self.x = 0

   def equal(self:Self, o : Self) -> Bool:
       return self.x == o.x

def f(x : Int):
    pass

p = Point() # Obj(Point){'equal': Function([Obj(){'x': Int}], Bool)}
q = Point() # ditto
b = p.equal(q) # q : Obj(Point){...} => Obj(){'x': Int}
print(b)
