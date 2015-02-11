class C:
    def __call__(self):
        pass

def f(x):
    x()

f(C())
