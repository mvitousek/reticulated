@fields({'a':Dyn, 'b' : Dyn})
class MyList:
    def __init__(self, a:Dyn, b:Dyn):
        self.a = a
        self.b = b

@fields({'a':Int, 'b':'MyListForce'})
class MyListForce:
    def __init__(self, a:Int, b:MyListForce):
        self.a = a
        self.b = b

def cast(x:MyListForce) -> Int:
    print(x.b.b.b.b.b.b)
    return x.a

init = MyList(5, None)
x = init
x = MyList(4, x)
x = MyList(3, x)
x = MyList(2, x)
x = MyList(1, x)
init.b = x

print(cast(init))
