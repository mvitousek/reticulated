#!/usr/bin/python3
import sys, argparse, ast, os.path, typing, flags, imp
import typecheck, runtime
from exc import UnimplementedException

## Type for 'open'ed files
if flags.PY_VERSION == 2:
    file_type = file
elif flags.PY_VERSION == 3:
    import io
    file_type = io.TextIOBase

def make_importer(typing_context):
    class ReticImporter:
        def __init__(self, path):
            self.path = path   
     
        def find_module(self, fullname):
            qualname = os.path.join(self.path, *fullname.split('.')) + '.py'
            try: 
                with open(qualname):
                    return self
            except IOError:
                return None

        def get_code(self, fileloc, filename):
            ast = py_parse(fileloc)
            typed_ast = py_typecheck(ast)
            return compile(typed_ast, filename, 'exec')

        def is_package(self, fileloc):
            return os.path.isdir(fileloc) and glob.glob(os.path.join(fileloc, '__init__.py*'))

        def load_module(self, fullname):    
            qualname = os.path.join(self.path, *fullname.split('.')) + '.py'
            code = self.get_code(qualname, fullname)
            ispkg = self.is_package(fullname)
            mod = sys.modules.setdefault(fullname, imp.new_module(fullname))
            mod.__file__ = qualname
            mod.__loader__ = self
            if ispkg:
                mod.__path__ = []
                mod.__package__ = fullname
            else:
                mod.__package__ = fullname.rpartition('.')[0]
            mod.__dict__.update(typing_context)
            exec(code, mod.__dict__)
            return mod
    return ReticImporter

def py_typecheck(py_ast):
    checker = typecheck.Typechecker()
    return checker.typecheck(py_ast)

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

    typed_ast = py_typecheck(py_ast)
    
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
        raise UnimplementedException('No such cast semantics', flags.SEMANTICS)

    code_context = {}
    code_context.update(typing.__dict__)
    code_context.update(cast_semantics.__dict__)
    code_context.update(runtime.__dict__)

    if flags.TYPECHECK_IMPORTS:
        sys.path_hooks.append(make_importer(code_context))
        
    exec(code, code_context)
    
    if answer_var != None:
        return code_context[answer_var]

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Typecheck and run a ' + 
                                     'Python program with type assertions')
    parser.add_argument('-v', '--verbosity', metavar='N', dest='warnings', nargs=1, default=[2], 
                        help='amount of information displayed at typechecking, 0-3')
    parser.add_argument('-e', '--no-static-errors', dest='static_errors', action='store_false', 
                        default=True, help='force statically-detected errors to trigger at runtime instead')
    parser.add_argument('-p', '--print', dest='output_ast', action='store_true', 
                        default=False, help='instead of executing the program, print out the modified program (comments will be lost)')
    typings = parser.add_mutually_exclusive_group()
    typings.add_argument('--casts-as-checks', dest='semantics', action='store_const', const='CAC',
                         help='use the casts-as-checks runtime semantics (the default)')
    typings.add_argument('--monotonic', dest='semantics', action='store_const', const='MONO',
                         help='use the monotonic objects runtime semantics')
    typings.add_argument('--guarded', dest='semantics', action='store_const', const='GUARDED',
                         help='use the guarded objects runtime semantics')
    typings.set_defaults(semantics='CAC')
    parser.add_argument('program', help='a Python program to be executed (.py extension required)')
    parser.add_argument('args', help='arguments to the program in question', nargs="*")

    args = parser.parse_args(sys.argv[1:])
    with open(args.program, 'r') as program:
        reticulate(program, prog_args=args.args, flag_sets=args)
