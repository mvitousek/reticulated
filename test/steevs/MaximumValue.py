# Here I set up the global variables.
MAX = 1
QUIT = 2

# Here I am setting up my main function to initiate variables,
# and to call the display funtion.
def main():

    # Variables.
    num1 = 0
    num2 = 0
    choice = 0

    # While loop to start menu.
    while choice != QUIT:
        display_menu()
        # Get the user's choice.
        choice = int(input('Enter your choice: '))

        # Start up choice decision structure.
        if choice == MAX:
            num1 = int(input('Enter the first number: '))
            num2 = int(input('Enter the second number: '))
            get_max(num1, num2)

        elif choice == QUIT:
            print('Exiting program...')

        else:
            print('Error: invalid selection.')

# Set up display menu function that prints the menu.
def display_menu():
        print('\t MENU')
        print('1) Get maximum of two values')
        print('2) Quit program')

        
# set up the get_max function.
def get_max(num1: Int, num2: Int):
    # Set up max num decision structure.
    if num1 < num2:
        print('The maximum of the two values is: ', num2)
    else:
        print('The maximum of the two values is: ', num1)
# Call the main function.
main()
