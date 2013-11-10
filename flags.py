VERBOSE = True
DEBUG_VISITOR = False
OPTIMIZED_INSERTION = True
STATIC_ERRORS = False
TYPECHECK_IMPORTS = False
SEMANTICS = 'CAC'
OUTPUT_AST = False

def set(args):
    global VERBOSE
    global STATIC_ERRORS
    global SEMANTICS
    global OUTPUT_AST
    VERBOSE = args.verbose
    STATIC_ERRORS = args.static_errors
    SEMANTICS = args.semantics
    OUTPUT_AST = args.output_ast
