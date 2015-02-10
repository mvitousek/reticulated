def g(foo):
    foo[0] = 'hello world'

def f(foo:List(int)):
    g(foo)
    print(foo[0])

foo = [42]
f(foo)
