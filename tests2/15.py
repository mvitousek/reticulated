class A:
	a = 1

class B(A):
	def foo(self:B) -> Int:
		return 2

class C(A):
	def bar(self:C) -> Int:
		return 3

@fields({'a' : A, 'b' : B, 'c' : C})
class D:
	a = A()
	b = B()
	c = C()
	def main(self:D) -> Int:
		self.b = B()
		self.a = self.b
		self.c = self.a
		return self.b.foo()


print(D().main())
