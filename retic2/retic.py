#!/usr/bin/env python3
from . import static, exc
import sys, argparse, os, os.path, ast

""" The Reticulated Python entry module. Run this on the command line!"""


# We don't have a REPL yet but we will.
def launch_repl():
    raise exc.UnimplementedException()

def main():
    parser = argparse.ArgumentParser(description='Typecheck and run a ' + 
                                     'Python program with type casts')
    parser.add_argument('-p', '--print', dest='output_ast', action='store_true', 
                        default=False, help='instead of executing the program, print out the modified program (comments and formatting will be lost)')
    typings = parser.add_mutually_exclusive_group()
    typings.add_argument('--transient', dest='semantics', action='store_const', const='TRANS',
                         help='use the casts-as-checks runtime semantics (the default)')
    typings.add_argument('--static-only', '--linting', '--noop', dest='semantics', action='store_const', const='NOOP',
                         help='do not perform runtime checks (static linting only)')
    typings.set_defaults(semantics='TRANS')
    parser.add_argument('program', help='a Python program to be executed (.py extension required)', default=None, nargs='?')
    parser.add_argument('args', help='arguments to the program in question (in quotes)', default='', nargs='?')

    args = parser.parse_args(sys.argv[1:])
    prog_args = args.args.split()
    if args.program is None:
        launch_repl()
    else:
        try:
            with open(args.program, 'r') as program:
                st, srcdata = static.parse_module(program)
                st = static.typecheck_module(st, srcdata)

                if args.semantics == 'TRANS':
                    st = static.transient_compile_module(st)
                elif args.semantics != 'NOOP':
                    raise UnimplementedException()

                if args.output_ast:
                    static.emit_module(st)
                else:
                    static.exec_module(st, srcdata)
        except IOError as e:
            print(e)
