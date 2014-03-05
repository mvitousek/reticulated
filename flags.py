import argparse, sys


"""
Warning levels:
0 -> Things that will cause errors
1 -> Things that won't be fully typechecked
2 -> Other notifications to users
"""
WARNINGS = 1

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
DEBUG_MESSAGES = True
DEBUG_MODES = set()#set([PROC,ENTRY])#set([IMP, SUBTY])

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
JOIN_BRANCHES = False

VERIFY_CONTEXTS = True
DEBUG_VISITOR = False
OPTIMIZED_INSERTION = True
STATIC_ERRORS = False
TYPECHECK_IMPORTS = True
TYPECHECK_LIBRARY = False
SEMANTICS = 'CAC'
OUTPUT_AST = False
TYPED_LITERALS = False
IMPORT_DEPTH = 2
PY_VERSION = sys.version_info.major
PY3_VERSION = sys.version_info.minor if PY_VERSION == 3 else None


def defaults(more=None):
    flags = argparse.Namespace(**{
            'warnings':[str(WARNINGS)],
            'static_errors':STATIC_ERRORS,
            'semantics':SEMANTICS,
            'output_ast':OUTPUT_AST,
            'typecheck_imports':TYPECHECK_IMPORTS
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
    WARNINGS = int(args.warnings[0])
    STATIC_ERRORS = args.static_errors
    SEMANTICS = args.semantics
    OUTPUT_AST = args.output_ast
    TYPECHECK_IMPORTS = args.typecheck_imports
