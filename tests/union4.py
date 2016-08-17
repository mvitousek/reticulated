def f(x:Union[int, str]):
    return x


def g(x):
    return f(x)

g(4.2)

