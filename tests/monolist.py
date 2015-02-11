class MonoList(list):
    def __setitem__(self, k, v):
        print('CSET', k, v)
        list.__setitem__(self,k,v)

    
def g(x):
    x.__setitem__(0, 'muh')
    #x[0] = 'muh'
def f(x:List(int)):
    g(x)
    print(x)

if True:
    x = MonoList([1,2,3])
    x[1] = 4
else: x = 1
f(x)

# def gp(x):
#     x.x = 'a'
# def fp(x:{'x':int}):
#     gp(x)

# class C:
#     pass

# if True:
#     xp = C()
#     xp.x = 10
# else: xp = 1

# fp(xp)
