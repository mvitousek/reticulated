def foo(x):
    return open(x, 'w')

def f(x:int):
    with foo('a') as x:
        print(__typeof(x + 42))
        x + 42

f(42)
