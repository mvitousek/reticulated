@fields({'x': int})
class B: pass

class C(B): pass

@fields({'x': str})
class D(C): pass
