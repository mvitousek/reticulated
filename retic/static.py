""" The static.py module is the main interface to the static features of Reticulated."""


from . import typecheck, return_checker, check_inserter, check_optimizer, check_compiler, transient, typing, exc, macro_expander, imports, importhook
from .astor import codegen
import ast, sys
from collections import namedtuple
import __main__

srcdata = namedtuple('srcdata', ['src', 'filename', 'parser', 'typechecker', 'compiler'])

def parse_module(input):
    """ Parse a Python source file and return it with the source info package (used in error handling)"""
    src = input.read()
    return ast.parse(src), srcdata(src=src, filename=input.name, parser=parse_module, typechecker=typecheck_module, compiler=transient_compile_module)
    
def typecheck_module(ast: ast.Module, srcdata)->ast.Module:
    """
    Performs typechecking. This set of passes should not copy the AST
    or mutate it structurally. It can, however, patch information into
    individual nodes. When this returns, if no static type errors have
    been raised, static type information should be patched into the
    AST as follows:

    - All instances of ast.expr should have a new 'retic_type'
      attribute, which contains a retic_ast.Type representing the
      static type of the expression
    - All instances of ast.FunctionDef should have a new
      'retic_return_type' attribute which contains a retic_ast.Type
      for the return type of the function
    - All instances of ast.arg should have a 'retic_type' attribute
      containing a retic_ast.Type indicating the expected static type
      of the argument.

    Ideally, this pass should not do anything specific to any
    semantics (i.e. transient or monotonic).

    """

    try:
        # In-place analysis passes
        imports.ImportProcessor().preorder(ast, sys.path, srcdata)
        typecheck.Typechecker().preorder(ast)
        return_checker.ReturnChecker().preorder(ast)
    except exc.StaticTypeError as e:
        exc.handle_static_type_error(e, srcdata)
    except exc.MalformedTypeError as e:
        exc.handle_malformed_type_error(e, srcdata)
    else:
        return ast
    
def transient_compile_module(st: ast.Module)->ast.Module:
    """
    Takes a type-annotated AST and produces a new AST with transient
    checks inserted.  Neither the input nor the output should contain
    non-standard AST nodes, but intermediate passes may. The overall
    structure is to insert retic_ast.Check nodes wherever needed,
    perform postprocessing on that, and then convert the Check nodes
    into regular Python AST nodes.
    """

    # Transient check insertion
    st = check_inserter.CheckInserter().preorder(st)
    st = check_optimizer.CheckRemover().preorder(st)
    
    # Emission to Python3 ast
    st = check_compiler.CheckCompiler().preorder(st)
    st = macro_expander.MacroExpander().preorder(st)
    return st
    
def emit_module(st: ast.Module, file=sys.stdout):
    """
    Emits a regular Python AST to source text, while adding imports to
    ensure that it can execute standalone
    """


    # Any 'from __future__ import ...' command has to be the first
    # line(s) of any module, so we have to insert our imports after
    # that.
    ins = 0

    while len(st.body) > ins and \
          isinstance(st.body[ins], ast.ImportFrom) and \
          st.body[ins].module == '__future__':
        ins += 1

    body = st.body[:]
    body.insert(ins, ast.ImportFrom(level=0, module='retic2.transient', names=[ast.alias(name='*', asname=None)]))

    print(codegen.to_source(ast.Module(body=body)), file=file)

def exec_module(ast: ast.Module, srcdata):
    """ Directly execute a Python AST. """
    code = compile(ast, srcdata.filename, 'exec')


    # This stuff sets up the environment that the program executes
    # in. We use __main__ to fool the program into thinking it's the
    # main module (i.e. has been executed directly by a python3
    # command) and then update the environment with definitions for
    # transient checks etc (as if the program had imported them)
    omain = __main__.__dict__.copy()
          
    __main__.__dict__.update(transient.__dict__)
    __main__.__dict__.update(typing.__dict__)
    __main__.__dict__.update(omain)
    __main__.__file__ = srcdata.filename

    
    # Installing the import hook, so that when things get imported they get typechecked
    importer = importhook.make_importer(__main__.__dict__)
    # if we want to re-typecheck everything that Reticulated already loaded
    sys.path_importer_cache.clear()
    sys.path_hooks.insert(0, importer)

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
