def h(x:List[Any]):
    x[0] = 'a'

def g(x:List[int])->int:
    return x[0]

def top(x:List[int]):
    h(x)
    g(x)

top([1])
