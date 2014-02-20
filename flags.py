import argparse, sys

WARNINGS = 2
DEBUG_VISITOR = False
OPTIMIZED_INSERTION = True
STATIC_ERRORS = False
TYPECHECK_IMPORTS = True
SEMANTICS = 'CAC'
OUTPUT_AST = False
TYPED_LITERALS = False
STRICT_MODE = False
PY_VERSION = sys.version_info.major

def defaults(more=None):
    flags = argparse.Namespace(**{
            'warnings':[str(WARNINGS)],
            'static_errors':STATIC_ERRORS,
            'semantics':SEMANTICS,
            'output_ast':OUTPUT_AST
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
    WARNINGS = int(args.warnings[0])
    STATIC_ERRORS = args.static_errors
    SEMANTICS = args.semantics
    OUTPUT_AST = args.output_ast
