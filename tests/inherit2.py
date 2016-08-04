class A(object):
    def __init__(self, top):
        pass

class B(A):
    def __init__(self, x, y):
        pass

class C(B):
    pass

print(__typeof(B(1,2).__init__))
C(1,2)
