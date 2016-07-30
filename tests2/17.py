class B:
	def foo(self:B) -> Int:
		return 2

class C:
	def foo(self:C) -> Dyn:
		return 2

@fields({'b' : B, 'c' : C})
class D:
	b = B()
	c = C()
	def main(self:D) -> Int:
		self.c = C()
		self.b = self.c
		return self.b.foo()


print(D().main())
