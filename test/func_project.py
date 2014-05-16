def f(x:List(Dyn)):
    x[0] = "hello"
def g(x:List(Int)):
    f(x)
g([1])
