@fields({'x':int})
class A: 
    def __init__(self):
        self.x = 20

class B:
    class C(A): pass

B.C().x
