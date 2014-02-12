import argparse


parser = argparse.ArgumentParser(description='Typecheck and run a ' + 
                                 'Python program with type assertions')
parser.add_argument('-v', '--verbosity', metavar='N', dest='warnings', nargs=1, default=[2], 
                    help='amount of information displayed at typechecking, 0-3')

parser.add_argument('program', help='a Python program to be executed (.py extension required)')

print(parser.parse_known_args(['-v1','k.py', '-3']))
