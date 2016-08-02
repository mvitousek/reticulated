def m(a:List[int]):
    def foo(m:int, n)->int:
        if len(a) < 10:
            a.append(n)
        return m
    return [foo(z, 'a') for z in a]

print(m([1,2,3]))
