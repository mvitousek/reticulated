class Point:
   x = -1
   def __init__(self):
      self.x = 0

   def move(self, dx:int):
      self.x = self.x + dx

a = 1         # a : int

def foo(x): return x

p = Point()   # p : Object(Point){'move': Function([Dyn], Dyn)}
p.move(foo('a'))     # a : int => Dyn
print(p.x)

