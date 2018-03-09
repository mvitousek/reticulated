@fields({'x':int})
class C:
  def __init__(self):
      self.x = 40

o = C()
C.x = 'hi'
print(C.x)
