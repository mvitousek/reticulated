class C:
    m = 10

def f(c):
    try:
        c.x
        print('WTF')
    except AttributeError:
        print('Yes.')

f(C())
