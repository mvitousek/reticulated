class A(object):
    def __init__(self, top):
        pass

class B(A):
    def __init__(self, x, y):
        pass

exit()
class C(B):
    pass

B(1,2)
C(1,2)
