def main():
    # This function gets user information for the variables weight, and height.
    weight = float(input('Enter your weight in pounds: '))
    height = float(input('Enter your height in inches: '))

    # This code signals the interpreter to go to function compute_BMI. 
    bmi = compute_BMI(weight, height)

    # This prints out the BMI chart.
    print('\nRECOMMENDED BMI CHART')
    print('BMI between 18.5 and 25: Ideal')
    print('BMI between 25 and 30: Overweight')
    print('BMI between 30 and 40: Obese, should lose weight')
    print('BMI greater than 40: Very obese, lose weight now')

    # This prints out the result of the formatted calculation.
    print('Your BMI is: ', format(bmi, '.1f'))

def compute_BMI(weight: Float, height: Float) -> Float:
    # This is the calculations for this function.
    bmi = weight * (703 / height ** 2)

    return bmi
    

# This calls the function.
main()
 
