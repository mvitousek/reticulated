# Global variables are defined.
STATE_TAX = .04
COUNTY_TAX = .02

def main():
    # Get the user's data.
    total_sales = float(input('Enter the total sales for the month: '))
    # Sends the interpreter to the next function.
    compute_tax(total_sales)

def compute_tax(total_sales: Float):

    # This code calculates and prints the state sales tax.
    state = total_sales * STATE_TAX
    print('The amount of state sales taxes: $', format(state, ',.2f'))

    # This code calculates and prints the county sales tax.
    county = total_sales * COUNTY_TAX
    print('The amount of county sales taxes: $', format(county, ',.2f'))

    # This code calculates and prints the total sales tax.
    total_taxes = state + county
    print('Total taxes: $', format(total_taxes, ',.2f'))

# Calls the main function.
main()
