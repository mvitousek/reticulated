#!/usr/bin/python3
import sys, argparse, ast, os.path, typing, flags, imp
import typecheck
from exc import UnimplementedException

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

def py_parse(in_file):
    with open(in_file, 'r') as f:
        program_string = f.read()
    return ast.parse(program_string)

def py_typecheck(py_ast):
    checker = typecheck.Typechecker()
    return checker.typecheck(py_ast)

def reticulate(in_file):
    mod = py_parse(in_file)
    mod = py_typecheck(mod)
    exec(mod, mod.__dict__)

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
flags.set(args)

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

if flags.TYPECHECK_IMPORTS:
    sys.path_hooks.append(make_importer(code_context))

exec(code, code_context)
