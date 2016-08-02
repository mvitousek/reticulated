class A:
    def m(self)->Tuple(A,A):
        return (self,self)

print(A().m())
