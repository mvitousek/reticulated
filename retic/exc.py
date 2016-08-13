import sys, os, traceback
from . import base_runtime_exception

# Exceptions and exception handling
class MalformedTypeError(Exception): 
    def __init__(self, node, msg:str):
        self.node = node
        self.msg = msg

class StaticTypeError(Exception): 
    def __init__(self, node, msg:str):
        self.node = node
        self.msg = msg

class StaticImportError(StaticTypeError): pass

class UnimplementedException(Exception): pass
class InternalReticulatedError(Exception): pass

def handle_static_type_error(error:StaticTypeError, srcdata:{'filename':str, 'src':str}, exit=True, stream=sys.stderr):
    print('\nStatic type error:', file=stream)
    if error.node:
        print('  File "{}", line {}'.format(srcdata.filename, error.node.lineno), file=stream)
        print('   ', srcdata.src.split('\n')[error.node.lineno-1], file=stream)
        print('   ', ' ' * error.node.col_offset + '^', file=stream)
    else:
        print('  File "{}", line 1'.format(srcdata.filename), file=stream)
    print(error.msg, file=stream)
    print(file=stream)
    if exit:
        quit()

def handle_malformed_type_error(error:MalformedTypeError, srcdata:{'filename':str, 'src':str}, exit=True, stream=sys.stderr):
    print('\nMalformed type annotation:', file=stream)
    if error.node:
        print('  File "{}", line {}'.format(srcdata.filename, error.node.lineno), file=stream)
        print('   ', srcdata.src.split('\n')[error.node.lineno-1], file=stream)
        print('   ', ' ' * error.node.col_offset + '^', file=stream)
    else:
        print('  File "{}", line 1'.format(srcdata.filename), file=stream)
    print(error.msg, file=stream)
    print(file=stream)
    if exit:
        quit()



def handle_runtime_error(ty, error, tb, exit=True):
    from . import retic
    retic_install_dir = os.path.dirname(retic.__file__)


    extract = traceback.extract_tb(tb)
    if not isinstance(error, base_runtime_exception.NormalRuntimeError) and \
       extract[-1][0].startswith(retic_install_dir):
        raise

    print('\nTraceback (most recent call last):', file=sys.stderr)

    lines = []
    for line in extract:
        if line[0].startswith(retic_install_dir):
            continue
        elif line[0].startswith('<frozen'):
            continue
        else: 
            lines.append(line)

    print(*traceback.format_list(lines), sep='', end='', file=sys.stderr)
    print(*traceback.format_exception_only(ty, error), end='', file=sys.stderr)
    if exit:
        quit(1)
