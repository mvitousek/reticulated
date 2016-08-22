class B:
    def f(x:int)->int:
        return 10

class H: pass

class C(H, B): pass

class D(C):
    def f(x:str):
        return 10

