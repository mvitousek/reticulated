class A:
    def a(self):
        pass


class B(A):
    b = 10
print(B().b)
print(B.b)
