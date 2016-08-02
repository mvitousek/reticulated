
def f(x:List[Tuple[int,str]])->List[str]:
    return [a * b for a, b in x]

f([(10, 'a')])[0]
