def g(x):
    return x

class A:
    def m(self)->Tuple['A','A']:
        return (self,g(A))
    def __repr__(self)->str:
        return 'A instance'

print(A().m()[1], __typeof(A().m()))
