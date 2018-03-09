foo = int
bar = foo

def f(x:bar)->bar:
    print(__typeof(x))
    return x

f(42)
