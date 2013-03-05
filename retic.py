#!/usr/bin/python3

import sys, argparse, ast, os.path
import typecheck
from typing import *

def py_parse(in_file):
    f = open(in_file, 'r')
    program_string = f.read()
    return ast.parse(program_string)

def py_typecheck(py_ast):
    checker = typecheck.Typechecker()
    return checker.typecheck(py_ast)

parser = argparse.ArgumentParser(description='Typecheck and run a ' + 
                                 'Python program with type assertions')
parser.add_argument('-v', '--verbose', dest='verbose', help='print extra information during typechecking',
                    action='store_const', const=True, default=False)
parser.add_argument('program', help='a Python program to be executed')
parser.add_argument('args', help='arguments to the program in question', nargs="*")

args = parser.parse_args(sys.argv[1:])

py_ast = py_parse(args.program)
typed_ast = py_typecheck(py_ast)
code = compile(typed_ast, args.program, 'exec')

sys.path.append(os.path.abspath(args.program)[0:-len(os.path.basename(args.program))])
sys.argv = [args.program] + args.args

exec(code)
