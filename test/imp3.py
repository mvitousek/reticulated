import imp4, threading, pickle, email, mailbox

def f(k:Function([Int], Int)):
    k(imp4.z)

x = f(imp4.x)
print(x)

def g(k:{'a':Function(NamedParameters([('p', int)]), int)})->(Function([int], int)):
    return k.a

print(g(imp4.C())(imp4.x(10)))
