@fields({'x':Int})
class Point:
   def __init__(self):
      self.x = 0

   def move(self : Point, dx : Int)->Void:
       self.x = self.x + dx

p = Point()   # p : Object(Point){'x': Int, 'move': Function(['dx:Int'], Void)}
p.move("hi")



