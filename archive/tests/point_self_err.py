class Point:
   def __init__(self):
      self.x = 0

   def move(self:Self, dx):
      f(self)
      self.x = self.x + dx

a = 1         # a : int
p = Point()   # p : Obj(Point){'move': Function(['dx:Dyn'], Dyn)}

def f(x):
   pass

f(p)

p.move(a)
print(p.x)

