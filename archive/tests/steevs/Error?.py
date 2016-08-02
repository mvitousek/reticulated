def main():
    value = 99
    print('The value is', value)
    change_me(value)
    print('Back in the main the value is', value)

def change_me(arg: Int):
    print('I am changing the value.')
    arg = "0"
    print('Now the value is', arg)

main()
