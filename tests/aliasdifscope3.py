class A:
    x = 20

x = A

class B:
    class C(x): pass
    print (__typeof(C().x))
