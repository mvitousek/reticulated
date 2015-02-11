class Point:
   def __init__(self):
      self.x = 0

   def move(self, dx):
      self.x = self.x + dx

a = 1         # a : int
p = Point()   # p : Object(Point){'move': Function([Dyn], Dyn)}
p.move(a)     # a : int => Dyn
print(p.x)

