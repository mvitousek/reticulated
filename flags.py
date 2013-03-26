VERBOSE = True
DEBUG_VISITOR = False
OPTIMIZED_INSERTION = False
STATIC_ERRORS = False

def set(args):
    global VERBOSE
    global STATIC_ERRORS
    VERBOSE = args.verbose
    STATIC_ERRORS = args.static_errors
