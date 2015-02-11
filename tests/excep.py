

class E(Exception):
    pass

class F(E):
    pass

if True:
    e = F
else: e = 44

try:
    raise e()
except F:
    print ('caught')
