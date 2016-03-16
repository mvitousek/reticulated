import argparse, sys


"""
Warning levels:
0 -> Things that will cause errors
1 -> Things that won't be fully typechecked
2 -> Other notifications to users
"""
WARNINGS = 0

"""
Debug flags:
IMP -> Importer
"""
IMP = 0
SUBTY = 1
PROC = 2
ENTRY = 3
DEBUG_MODE_NAMES = {
    IMP : 'Importer',
    SUBTY : 'Subtyping',
    PROC : 'Procedures',
    ENTRY : 'Class entry'
    }

SEM_NAMES = {
    'TRANS' : 'transient',
    'MONO' : 'monotonic',
    'GUARDED' : 'guarded',
    'NOOP' : 'noop',
    'MGDTRANS': 'managed transient'
}

DEBUG_MESSAGES = True
DEBUG_MODES = set([SUBTY])#set([PROC,ENTRY])#set([IMP, SUBTY])

IGNORED_MODULES = {}#{'bdb', 'configparser'}

VERSION = '0.1.0a1'

# Feature flags
REJECT_WEIRD_CALLS = False
REJECT_TYPED_DELETES = False
CHECK_ACCESS = True
FLAT_PRIMITIVES = False
CLOSED_CLASSES = False
MORE_BINOP_CHECKING = False
SUBCLASSES_REQUIRE_SUBTYPING = False
PARAMETER_NAME_CHECKING = False
MERGE_KEEPS_SOURCES = False
JOIN_BRANCHES = True
TYPED_LITERALS = True
TYPED_SHAPES = True
INITIAL_ENVIRONMENT = False
FINAL_PARAMETERS = True
TYPED_LAMBDAS = True
REMOVE_ANNOTATIONS = True
MINIMIZE_ERRORS = False

SQUELCH_ERROR_STRINGS = False
INLINE_DUMMY_DEFS = False
SQUELCH_MESSAGES = False
VERIFY_CONTEXTS = False
DEBUG_VISITOR = False
OPTIMIZED_INSERTION = True
STATIC_ERRORS = True
TYPECHECK_IMPORTS = True
TYPECHECK_LIBRARY = False
SEMANTICS = 'TRANS'
OUTPUT_AST = False
IMPORT_DEPTH = 15
CHECK_DEPTH = 10
DRY_RUN = False
SEMI_DRY = False
PY_VERSION = sys.version_info.major
PY3_VERSION = sys.version_info.minor if PY_VERSION == 3 else None
DIE_ON_STATIC_ERROR = True
NULLABLE = True
PATH = ''
        

def defaults(more=None):
    flags = argparse.Namespace(**{
            'warnings':[str(WARNINGS)],
            'static_errors':STATIC_ERRORS,
            'semantics':SEMANTICS,
            'output_ast':OUTPUT_AST,
            'typecheck_imports':TYPECHECK_IMPORTS,
            'die_on_static_error':DIE_ON_STATIC_ERROR
            })
    if more != None:
        for k in more:
            setattr(flags, k, more[k])
    return flags

def set(args):
    global WARNINGS
    global STATIC_ERRORS
    global SEMANTICS
    global OUTPUT_AST
    global TYPECHECK_IMPORTS
    global DIE_ON_STATIC_ERROR
    WARNINGS = int(args.warnings[0])
    STATIC_ERRORS = args.static_errors
    SEMANTICS = args.semantics
    OUTPUT_AST = args.output_ast
    TYPECHECK_IMPORTS = args.typecheck_imports
    DIE_ON_STATIC_ERROR = args.die_on_static_error
