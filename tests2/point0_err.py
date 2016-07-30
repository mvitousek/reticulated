class Point:
   def __init__(self):
       self.x = 0

   def move(self, dx : str):
       self.x = self.x + dx

a = 1
p = Point()
p.move(a)
print(p.x)

