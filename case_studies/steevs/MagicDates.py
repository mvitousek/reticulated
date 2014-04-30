def main():
    month = int(input('Enter the month(mm): '))
    day = int(input('Enter the day(dd): '))
    year = int(input('Enter the year(yy): '))

    check_magic(month, day, year)

def check_magic(month: String, day: String, year: String):
    if month * day == year:
        print('The date,')
        print(month, day, year, sep = '/')
        print('is a magic date.')
    else:
        print('The date,')
        print(month, day, year, sep = '/')
        print('is not a magic date.')

main()
