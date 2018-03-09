class B:
    def f(x:int)->int:
        return 10

class C(B): pass

class D(C):
    def f(x:str):
        return 10

