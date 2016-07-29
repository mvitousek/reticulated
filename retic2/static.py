from . import typecheck, return_checker, check_inserter, check_optimizer, check_compiler, transient, typing, exc
from .astor import codegen
import ast, sys
from collections import namedtuple
import __main__

srcdata = namedtuple('srcdata', ['src', 'filename'])

def parse_module(input):
    src = input.read()
    return ast.parse(src), srcdata(src=src, filename=input.name)
    
def typecheck_module(ast: ast.Module, srcdata)->ast.Module:
    try:
        # In-place analysis passes
        typecheck.Typechecker().preorder(ast)
        return_checker.ReturnChecker().preorder(ast)
    except exc.StaticTypeError as e:
        exc.handle_static_type_error(e, srcdata)
    except exc.MalformedTypeError as e:
        exc.handle_malformed_type_error(e, srcdata)
    else:
        return ast
    
def transient_compile_module(st: ast.Module)->ast.Module:
    # Transient check insertion
    
    st = check_inserter.CheckInserter().preorder(st)
    st = check_optimizer.CheckRemover().preorder(st)
    
    # Emission to Python3 ast
    st = check_compiler.CheckCompiler().preorder(st)
    return st
    
def emit_module(st: ast.Module, file=sys.stdout):
    ins = 0

    while len(st.body) > ins and \
          isinstance(st.body[ins], ast.ImportFrom) and \
          st.body[ins].module == '__future__':
        ins += 1

    body = st.body[:]
    body.insert(ins, ast.ImportFrom(level=0, module='retic2.transient', names=[ast.alias(name='*', asname=None)]))

    print(codegen.to_source(ast.Module(body=body)), file=file)

def exec_module(ast: ast.Module, srcdata):
    code = compile(ast, srcdata.filename, 'exec')

    omain = __main__.__dict__.copy()
          
    code_context = {}
    __main__.__dict__.update(transient.__dict__)
    __main__.__dict__.update(typing.__dict__)
    __main__.__dict__.update(omain)
    __main__.__file__ = srcdata.filename
    try:
        exec(code, __main__.__dict__)
    finally:
        # Fix up __main__, in case called again.
        killset = []
        __main__.__dict__.update(omain)
        for x in __main__.__dict__:
            if x not in omain:
                killset.append(x)
        for x in killset:
            del __main__.__dict__[x]
    

