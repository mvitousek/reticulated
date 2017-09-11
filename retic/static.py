""" The static.py module is the main interface to the static features of Reticulated."""


from . import typecheck, return_checker, check_inserter, check_optimizer, check_compiler, transient, typing, exc, macro_expander, imports, importhook, base_runtime_exception, inferencer, scope, type_localizer, flags, opt_check_compiler, opt_transient, annot_stripper
from .trust import cscopes, constrgen, usage_check_inserter, return_constrgen, solve, opt, openworld, checkcounter
from .astor import codegen
import ast, sys
from collections import namedtuple
import __main__

srcdata = namedtuple('srcdata', ['src', 'filename'])

def parse_module(input):
    """ Parse a Python source file and return it with the source info package (used in error handling)"""
    src = input.read()
    return ast.parse(src), srcdata(src=src, filename=input.name)
    
def typecheck_module(st: ast.Module, srcdata, topenv=None, exit=True)->ast.Module:
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
    - All instances of ast.Module should have a 'retic_type' attribute
      as above

    Ideally, this pass should not do anything specific to any
    semantics (i.e. transient or monotonic).

    """

    try:
        # Determine the types of imported values, by finding and
        # typechecking the modules being imported.
        imports.ImportProcessor().preorder(st, sys.path, srcdata)
        # Gather the bound variables for every scope
        scope.ScopeFinder().preorder(st, topenv)
        # Perform most of the typechecking
        typecheck.Typechecker().preorder(st)
        # Make sure that all functions return and that all returned
        # values match the return type of the calling function
        return_checker.ReturnChecker().preorder(st)

    except exc.StaticTypeError as e:
        exc.handle_static_type_error(e, srcdata, exit=exit)
    except exc.MalformedTypeError as e:
        exc.handle_malformed_type_error(e, srcdata, exit=exit)
    else:
        return st
    
def transient_compile_module(st: ast.Module)->ast.Module:
    """
    Takes a type-annotated AST and produces a new AST with transient
    checks inserted.  Neither the input nor the output should contain
    non-standard AST nodes, but intermediate passes may. The overall
    structure is to insert retic_ast.Check nodes wherever needed,
    perform postprocessing on that, and then convert the Check nodes
    into regular Python AST nodes.
    """
    st = annot_stripper.AnnotationStripper().preorder(st)
    # Transient check insertion
    st = check_inserter.CheckInserter().preorder(st)
    st = macro_expander.MacroExpander().preorder(st)

    optimize = True
    stats = True
    if optimize:
        if stats:
            old_st = st
        st = usage_check_inserter.UsageCheckInserter().preorder(st)
        cscopes.ImportProcessor().preorder(st)
        constraints = cscopes.ScopeFinder().preorder(st, None)
        constraints |= constrgen.ConstraintGenerator().preorder(st)
        constraints |= return_constrgen.ReturnConstraintGenerator().preorder(st)
        #    constraints |= openworld.OpenWorld().preorder(st)
        #    print(constraints)
        try:
            constraints = solve.normalize(constraints, st.retic_cctbl)
        except solve.BailOut as ex:
            print('#Could not solve constraint system:', *ex.args)
            constraints = []

        st = opt.CheckRemover().preorder(st, constraints)
        if stats:
            stn = checkcounter.CheckCounter().preorder(st)
            old_st = check_optimizer.CheckRemover().preorder(old_st)
            ostn = checkcounter.CheckCounter().preorder(old_st)
            print('#{}/{} checks remaining ({} removed, for a {}% reduction)'.format(stn, ostn, ostn-stn, (1-(stn/(ostn if ostn else 1)))*100))
        
    else: st = check_optimizer.CheckRemover().preorder(st)
    
    # Emission to Python3 ast
    type_localizer.TypeLocalizer().preorder(st)
    if not flags.optimized():
        st = check_compiler.CheckCompiler().preorder(st)
    else:
        st = opt_check_compiler.CheckCompiler().preorder(st)
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
    if not flags.optimized():
        body.insert(ins, ast.ImportFrom(level=0, module='retic.transient', names=[ast.alias(name='*', asname=None)]))
    else:
        body.insert(ins, ast.ImportFrom(level=0, module='retic.opt_transient', names=[ast.alias(name='*', asname=None)]))


    print(codegen.to_source(ast.Module(body=body)), file=file)

def exec_module(ast:ast.Module, srcdata):
    code = compile(ast, srcdata.filename, 'exec')

    nmain, omain = setup_main_dict(srcdata)
    setup_import_hook(nmain)

    try:
        exec(code, nmain)

    # These catches are for if we do load-time typechecking of an import and encounter a type error.
    except exc.StaticTypeError as e:
        exc.handle_static_type_error(e, srcdata)
    except exc.MalformedTypeError as e:
        exc.handle_malformed_type_error(e, srcdata)
    finally:
        # Fix up __main__, in case called again.
        cleanup_main_dict(omain)

def repl_eval_module(ast, srcdata, main):
    code = compile(ast, srcdata.filename, 'eval')
    try:
        return eval(code, main)
    # These catches are for if we do load-time typechecking of an import and encounter a type error.
    except exc.StaticTypeError as e:
        exc.handle_static_type_error(e, srcdata, exit=False)
    except exc.MalformedTypeError as e:
        exc.handle_malformed_type_error(e, srcdata, exit=False)
    return None

def repl_exec_module(ast, srcdata, main):
    code = compile(ast, srcdata.filename, 'exec')
    try:
        exec(code, main)
    # These catches are for if we do load-time typechecking of an import and encounter a type error.
    except exc.StaticTypeError as e:
        exc.handle_static_type_error(e, srcdata, exit=False)
    except exc.MalformedTypeError as e:
        exc.handle_malformed_type_error(e, srcdata, exit=False)

def setup_main_dict(srcdata):
    # This stuff sets up the environment that the program executes
    # in. We use __main__ to fool the program into thinking it's the
    # main module (i.e. has been executed directly by a python3
    # command) and then update the environment with definitions for
    # transient checks etc (as if the program had imported them)
    omain = __main__.__dict__.copy()

    if not flags.optimized():
        __main__.__dict__.update(transient.__dict__)
    else:
        __main__.__dict__.update(opt_transient.__dict__)
    __main__.__dict__.update(typing.__dict__)
    __main__.__dict__.update(omain)
    __main__.__file__ = srcdata.filename

    return __main__.__dict__, omain
    
def setup_import_hook(dict):
    # Installing the import hook, so that when things get imported they get typechecked
    importer = importhook.make_importer(dict)
    # if we want to re-typecheck everything that Reticulated already loaded
    sys.path_importer_cache.clear()
    sys.path_hooks.insert(0, importer)

def cleanup_main_dict(omain):
    # Fix up __main__, in case called again.
    killset = []
    __main__.__dict__.update(omain)
    for x in __main__.__dict__:
        if x not in omain:
            killset.append(x)
    for x in killset:
        del __main__.__dict__[x]
    
