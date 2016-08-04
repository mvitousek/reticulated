
class A:
  def f(a:'A', b:'A')->List('A'):
    return [a, b]

class B:

    vals = [A(), A()]

    def g(self: 'B'):
        [a1, a2] = (self.vals[0]).f(1)

b = B()
b.g()
