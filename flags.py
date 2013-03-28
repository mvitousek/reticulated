VERBOSE = True
DEBUG_VISITOR = False
OPTIMIZED_INSERTION = False
STATIC_ERRORS = False
TYPECHECK_IMPORTS = True
SEMANTICS = 'CAC'


def set(args):
    global VERBOSE
    global STATIC_ERRORS
    global SEMANTICS
    VERBOSE = args.verbose
    STATIC_ERRORS = args.static_errors
    SEMANTICS = args.semantics
