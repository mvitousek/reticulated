def m(a:List(int)):
    def foo(m:int)->int:
        a.append('a')
        return m
    [foo(m) for z in a]

m([1,2,3])
