BASE_HOURS = 40
OT_MULTIPLIER = 1.5

def main():
    hours_worked = float(input('Enter the number of hours worked: '))

    pay_rate = float(input('Enter the hourly pay rate: '))

    if hours_worked > BASE_HOURS:
        calc_pay_with_OT(hours_worked, pay_rate)

    else:
        calc_regular_pay(hours_worked, pay_rate)


def calc_pay_with_OT(hours: Float, rate: Float):
    overtime_hours = hours - BASE_HOURS

    overtime_pay = overtime_hours * rate * OT_MULTIPLIER

    gross_pay = BASE_HOURS * rate + overtime_pay

    print('The gross pay is $', format(gross_pay, ',.2f'), sep = '')


def calc_regular_pay(hours: Float, rate: Float):
    gross_pay = hours * rate

    print('The gross pay is $', format(gross_pay, ',.2f'), sep = '')

main()
