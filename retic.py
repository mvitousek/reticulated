#!/usr/bin/python3
import sys, argparse, ast, os.path, typing, flags
import typecheck, runtime
from exc import UnimplementedException
from importer import make_importer

## Type for 'open'ed files
if flags.PY_VERSION == 2:
    file_type = file
elif flags.PY_VERSION == 3:
    import io
    file_type = io.TextIOBase

def reticulate(input, prog_args=None, flag_sets=None, answer_var=None, **individual_flags):
    if prog_args == None:
        prog_args = []
    if isinstance(flag_sets, type(None)):
        flag_sets = flags.defaults(individual_flags)
    flags.set(flag_sets)
    
    if isinstance(input, str):
        py_ast = ast.parse(input)
        module_name = '__text__'
    elif isinstance(input, ast.Module):
        py_ast = input
        module_name = '__ast__'
    elif isinstance(input, file_type):
        py_ast = ast.parse(input.read())
        module_name = input.name
        sys.path.append(os.path.abspath(module_name)[0:-len(os.path.basename(module_name))])

    checker = typecheck.Typechecker()
    typed_ast, _ = checker.typecheck(py_ast, module_name, 0)
    
    if flags.OUTPUT_AST:
        import astor.codegen
        print(astor.codegen.to_source(typed_ast))
        return
    
    code = compile(typed_ast, module_name, 'exec')

    sys.argv = [module_name] + prog_args

    if flags.SEMANTICS == 'CAC':
        import cast_as_check as cast_semantics
    elif flags.SEMANTICS == 'MONO':
        import monotonic as cast_semantics
    elif flags.SEMANTICS == 'GUARDED':
        import guarded as cast_semantics
    else:
        assert False, 'Unknown semantics ' + flags.SEMANTICS

    code_context = {}
    code_context.update(typing.__dict__)
    code_context.update(cast_semantics.__dict__)
    code_context.update(runtime.__dict__)
    
    if flags.TYPECHECK_IMPORTS:
        importer = make_importer(code_context)
        sys.path_importer_cache.clear()
        sys.path_hooks.append(importer)
        
    exec(code, code_context)
    
    if answer_var != None:
        return code_context[answer_var]

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Typecheck and run a ' + 
                                     'Python program with type casts')
    parser.add_argument('-v', '--verbosity', metavar='N', dest='warnings', nargs=1, default=[flags.WARNINGS], 
                        help='amount of information displayed at typechecking, 0-3')
    parser.add_argument('-e', '--no-static-errors', dest='static_errors', action='store_false', 
                        default=True, help='force statically-detected errors to trigger at runtime instead')
    parser.add_argument('-p', '--print', dest='output_ast', action='store_true', 
                        default=False, help='instead of executing the program, print out the modified program (comments and formatting will be lost)')
    typings = parser.add_mutually_exclusive_group()
    typings.add_argument('--casts-as-checks', dest='semantics', action='store_const', const='CAC',
                         help='use the casts-as-checks runtime semantics (the default)')
    typings.add_argument('--monotonic', dest='semantics', action='store_const', const='MONO',
                         help='use the monotonic objects runtime semantics')
    typings.add_argument('--guarded', dest='semantics', action='store_const', const='GUARDED',
                         help='use the guarded objects runtime semantics')
    typings.set_defaults(semantics='CAC')
    parser.add_argument('program', help='a Python program to be executed (.py extension required)')
    parser.add_argument('args', help='arguments to the program in question (in quotes)', default='', nargs='?')

    args = parser.parse_args(sys.argv[1:])
    with open(args.program, 'r') as program:
        reticulate(program, prog_args=args.args.split(), flag_sets=args)
