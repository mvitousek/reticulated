def main():
    month = 12
    day = 03
    year = 08

    check_magic(month, day, year)

def check_magic(month: Dyn, day: Dyn, year: Int):
    if month * day == year:
        print('The date,')
        print(month, day, year, sep = '/')
        print('is a magic date.')
    else:
        print('The date,')
        print(month, day, year, sep = '/')
        print('is not a magic date.')

main()
