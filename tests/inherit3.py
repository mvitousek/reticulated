class A:
    def __init__(self, top):
        pass

class B(A):
    def __init__(self, x, y):
        pass

class C(B):
    pass

B(1)
C(1,2)
