#!/usr/bin/python3

import sys, argparse, ast, os.path, typing
import typecheck
from exc import UnimplementedException

def py_parse(in_file):
    with open(in_file, 'r') as f:
        program_string = f.read()
    return ast.parse(program_string)

def py_typecheck(py_ast):
    checker = typecheck.Typechecker()
    return checker.typecheck(py_ast)

parser = argparse.ArgumentParser(description='Typecheck and run a ' + 
                                 'Python program with type assertions')
parser.add_argument('-v', '--verbose', dest='verbose', action='store_true', default=False, 
                    help='print extra information during typechecking')
parser.add_argument('-e', '--no-static-errors', dest='static_errors', action='store_false', 
                    default=True, help='force statically-detected errors to trigger at runtime instead')
typings = parser.add_mutually_exclusive_group()
typings.add_argument('--casts-as-checks', dest='semantics', action='store_const', const='CAC',
                     help='use the casts-as-checks runtime semantics (the default)')
typings.add_argument('--monotonic', dest='semantics', action='store_const', const='MONO',
                     help='use the monotonic objects runtime semantics')
typings.add_argument('--guarded', dest='semantics', action='store_const', const='GUARDED',
                     help='use the guarded objects runtime semantics')
typings.set_defaults(semantics='CAC')
parser.add_argument('program', help='a Python program to be executed')
parser.add_argument('args', help='arguments to the program in question', nargs="*")

args = parser.parse_args(sys.argv[1:])

py_ast = py_parse(args.program)
typed_ast = py_typecheck(py_ast)
code = compile(typed_ast, args.program, 'exec')

sys.path.append(os.path.abspath(args.program)[0:-len(os.path.basename(args.program))])
sys.argv = [args.program] + args.args

if args.semantics == 'CAC':
    import cast_as_check as cast_semantics
else:
    raise UnimplementedException()

code_context = {}
code_context.update(typing.__dict__)
code_context.update(cast_semantics.__dict__)
exec(code, code_context)
