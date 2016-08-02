class A:
  def f(self:A, xs:List(A))->Int:
    return 0

class B(A):
  def f(self:B, bs:List(Int))->Int:
    return 1
