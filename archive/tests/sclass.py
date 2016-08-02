class C:
    x = 10
    def __str__(self):
        return 'C'

def f(x:C.Class)->C:
    return x()

print(f(C))
