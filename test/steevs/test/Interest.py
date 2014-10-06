def main():
    show_interest(rate = 0.01, periods = 10, principal = 10000.0)

def show_interest(principal: Float, rate: Int, periods: Int):
    interest = principal * rate * periods
    print('The simple interest will be $', \
          format(interest, ',.2f'), \
          sep='')

main()
