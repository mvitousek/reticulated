def f():
    return 40

if True:
    m = f
else: m = 10

def hi(x:Function([], Void)):
    x()

hi(m)
