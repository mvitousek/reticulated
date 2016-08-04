class A: pass

engine = A()
if True:
    de = engine
else:
    de = False

print(__typeof(de))
