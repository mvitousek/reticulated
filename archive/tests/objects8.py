@fields({'x':int})
class C:
    x = 10
    def f(self:Self)->str:
        return self.x
