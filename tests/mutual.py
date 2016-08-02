@fields({'b':Board})
class Zob:
    def __init__(self, b:Board):
        self.b = b

@fields({'z':Zob})
class Board:
    def __init__(self):
        self.z = Zob(self)

def f(b:Board):
    pass

f(Board())
