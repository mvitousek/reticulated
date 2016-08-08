@fields({'x':int})
class C:
    x = 10
    def f(self:'C')->str:
        return self.x
