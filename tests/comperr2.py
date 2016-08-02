def m(a:List[int]):
    def foo(m:int)->int:
        if len(a) < 10:
            a.append('a')
        return m
    return [foo(m) for z in a]

print(m([1,2,3]))
