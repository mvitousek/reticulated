# Set up main function.
def main():

    # Set up variable.
    days = int(input('Enter the number of days worked: '))

    # Initialize next function.
    create_table(days)

# Call next function.
def create_table(days: String):

    # Print titles.
    print('Day\tSalary\t\tTotal Pay')
    print('-------------------------------------')

    # Initialize variables.
    time = 0
    pennies = 1
    total = pennies

    # Set up for loop.
    for time in range(days):
        # Set up counts.
        time += 1 
        total += pennies
        
        # Set up print statments.
        print(time, '\t$', format(pennies / 100, ',.2f'), '\t\t$', \
              format(total / 100, ',.2f'))

        # Change penny count.
        pennies += pennies
        
# Call main funtion.
main()
