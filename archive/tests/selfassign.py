class C:
    g = 30
    def f(self, other:Self):
        if True:
            m = other
        else: m = 40
        return m.g

C().f(C())
