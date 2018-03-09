
class C:
    def __init__(self,x):
        self.x = x

    def m(self,D:C.Class):
        print(self.x)
        return D('two')

a = C('one')    # an instance of a
b = a.m(C)      # another instance of a
print(a.x)
print(b.x)
