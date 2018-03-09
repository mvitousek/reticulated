def f(x:List[Any]):
    x[0] = "hello"
def g(x:List[int]):
    f(x)
    x[0]
g([1])
