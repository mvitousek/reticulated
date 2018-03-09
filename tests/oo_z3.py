class A:
    def m(self)->Tuple['A','A']:
        return (self,self)
    def __repr__(self)->str:
        return 'A instance'

print(A().m(), __typeof(A().m()))
