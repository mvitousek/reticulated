@fields({'x':int})
class C:
  def __init__(self:Self):
      self.x = 'hi'

o = C()
y = o.x + 2
print(y)
