class A: 
    x = 20

class B:
    class C(A): pass

B.C().x
