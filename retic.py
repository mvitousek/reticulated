#!/usr/bin/python

import sys, argparse, ast
import typecheck

def py_parse(in_file):
    return ast.parse(in_file)

def typecheck(ast):
    checker = typecheck.Typechecker()
    checker.typecheck(ast)

parser = argparse.ArgumentParser(description='Typecheck and run a ' + 
                                 'Python program with type assertions')
parser.add_argument('-w', '--weak', help='don\'t add assertions at object read sites.',
                    action='store_const', const=True, default=False)
parser.add_argument('program', help='a Python program to be executed')

args = parser.parse_args(sys.argv[1:])

data = py_parse(args.program)
typecheck(data)
