@fields({'x':int})
class C:
  def __init__(self):
      self.x = 40

o = C()
y = o.x + 2
print(y)
