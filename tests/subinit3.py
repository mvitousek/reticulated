class A: pass

class C:
    def __init__(self, x:int):
        pass

class D(A, C): pass

D(1)
