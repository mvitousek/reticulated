import imp2, os

@retic_typed(Function([Function([Int], Int)], Void))
def f(k):
    k(imp2.x)

f(imp2.z)
