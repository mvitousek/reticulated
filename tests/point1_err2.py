class Point:
   x=10
   def __init__(self):
       self.x = 0

   def equal(self:'Point', o : {'x':int,'foo':int}) -> bool:
       return self.x == o.x

def f(x : int):
    pass

p = Point()    # p : Object(Point){'equal': Function([Object(){'x': Int}], Bool)}
q = Point()
b = p.equal(q) # q : Obj(Point){...} => {'x':int,'foo':int}, this should fail statically!
print(b)

