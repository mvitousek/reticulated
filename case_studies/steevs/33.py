def main():
    a = 2
    b = 4
    c = 6
    print('Value a = ', a, 'Value b = ', b, 'Value c = ', c)
    my_function(a, b, c)

def  my_function (a: Int, b: Int, c: Int):
    d = (a + c ) / b
    print(d)

main()
