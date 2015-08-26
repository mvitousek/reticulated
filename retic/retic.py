#!/usr/bin/env python3
from __future__ import print_function
from . import typing, flags, utils, exc, repl, typecheck, runtime, static
import sys, argparse, ast, os.path
import __main__
from .importer import make_importer

if flags.PY_VERSION == 3:
    from .exec3 import _exec
else: from .exec2 import _exec

## Type for 'open'ed files
if flags.PY_VERSION == 2:
    file_type = file
elif flags.PY_VERSION == 3:
    import io
    file_type = io.TextIOBase

def reticulate(input, prog_args=None, flag_sets=None, answer_var=None, **individual_flags):
    if prog_args == None:
        prog_args = []
    if flag_sets is None:
        flag_sets = flags.defaults(individual_flags)
    flags.set(flag_sets)
    
    if input is None:
        return repl.repl()
    elif isinstance(input, str):
        py_ast = ast.parse(input)
        module_name = '__text__'
    elif isinstance(input, ast.Module):
        py_ast = input
        module_name = '__ast__'
    elif isinstance(input, file_type):
        py_ast = ast.parse(input.read())
        module_name = input.name
        sys.path.insert(1, os.path.abspath(module_name)[0:-len(os.path.basename(module_name))])

    type_system = static.StaticTypeSystem()

    if flags.DRY_RUN:
        typed_ast = py_ast
    else:
        try:
            typed_ast, _ = type_system.typecheck_module(py_ast, module_name)
        except exc.StaticTypeError as e:
            utils.handle_static_type_error(e, exit=flags.DIE_ON_STATIC_ERROR)
            return
    
    if flags.OUTPUT_AST:
        from . import unparse
        unparse.unparse(typed_ast)
        return
    
    code = compile(typed_ast, module_name, 'exec')

    sys.argv = [module_name] + prog_args

    if flags.SEMANTICS == 'TRANS':
        from . import transient as cast_semantics
    elif flags.SEMANTICS == 'MONO':
        from . import monotonic as cast_semantics
    elif flags.SEMANTICS == 'GUARDED':
        from . import guarded as cast_semantics
    elif flags.SEMANTICS == 'NOOP':
        from . import noop as cast_semantics
    else:
        assert False, 'Unknown semantics ' + flags.SEMANTICS
        

    omain = __main__.__dict__.copy()

    code_context = {}
    code_context.update(typing.__dict__)
    if not flags.DRY_RUN:
        code_context.update(cast_semantics.__dict__)
        code_context.update(runtime.__dict__)
        
    __main__.__dict__.update(code_context)
    __main__.__dict__.update(omain)
    __main__.__file__ = module_name
    try:
        if flags.TYPECHECK_IMPORTS:
            importer = make_importer(code_context, type_system)
            if flags.TYPECHECK_LIBRARY:
                sys.path_importer_cache.clear()
            sys.path_hooks.insert(0, importer)

        try:
            _exec(code, __main__.__dict__)
        except Exception:
            utils.handle_runtime_error(exit=True)
            return
        except exc.RuntimeTypeError:
            utils.handle_runtime_error(exit=True)
            return

        if answer_var != None:
            return code_context[answer_var]
    finally:
        # Fix up __main__, in case reticulate called again.
        killset = []
        __main__.__dict__.update(omain)
        for x in __main__.__dict__:
            if x not in omain:
                killset.append(x)
        for x in killset:
            del __main__.__dict__[x]

def main():
    parser = argparse.ArgumentParser(description='Typecheck and run a ' + 
                                     'Python program with type casts')
    parser.add_argument('-v', '--verbosity', metavar='N', dest='warnings', nargs=1, default=[flags.WARNINGS], 
                        help='amount of information displayed at typechecking, 0-3')
    parser.add_argument('-e', '--no-static-errors', dest='static_errors', action='store_false', 
                        default=True, help='force statically-detected errors to trigger at runtime instead')
    parser.add_argument('-p', '--print', dest='output_ast', action='store_true', 
                        default=False, help='instead of executing the program, print out the modified program (comments and formatting will be lost)')
    parser.add_argument('-ni', '--no-imports', dest='typecheck_imports', action='store_false', 
                        default=True, help='do not typecheck or cast-insert imported modules')
    typings = parser.add_mutually_exclusive_group()
    typings.add_argument('--transient', '--casts-as-check', dest='semantics', action='store_const', const='TRANS',
                         help='use the casts-as-checks runtime semantics (the default)')
    typings.add_argument('--monotonic', dest='semantics', action='store_const', const='MONO',
                         help='use the monotonic objects runtime semantics')
    typings.add_argument('--guarded', dest='semantics', action='store_const', const='GUARDED',
                         help='use the guarded objects runtime semantics')
    typings.add_argument('--static-only', '--linting', '--noop', dest='semantics', action='store_const', const='NOOP',
                         help='do not perform runtime checks (static linting only)')
    typings.set_defaults(semantics='TRANS')
    parser.add_argument('program', help='a Python program to be executed (.py extension required)', default=None, nargs='?')
    parser.add_argument('args', help='arguments to the program in question (in quotes)', default='', nargs='?')

    args = parser.parse_args(sys.argv[1:])
    args.die_on_static_error = True
    if args.program is None:
        reticulate(None, prog_args=args.args.split(), flag_sets=args)
    else:
        try:
            with open(args.program, 'r') as program:
                reticulate(program, prog_args=args.args.split(), flag_sets=args)
        except IOError as e:
            print(e)
