class A:
  a = None

  def __init__(self:int):
    self.a = 4

  def f(self:int):
    return self.a + 1

a = A()
print(a.f())
