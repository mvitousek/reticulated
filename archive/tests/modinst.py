class C:
    def gell(self):
        self.hello = None
    def hello(self):
        pass

def f(x:Function(DynParameters, Dyn)):
    x()

p = C()
p.gell()
f(p.hello)
