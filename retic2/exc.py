import sys

# Exceptions and exception handling
class MalformedTypeError(Exception): 
    def __init__(self, node, msg:str):
        self.node = node
        self.msg = msg

class StaticTypeError(Exception): 
    def __init__(self, node, msg:str):
        self.node = node
        self.msg = msg

class UnimplementedException(Exception): pass
class InternalReticulatedError(Exception): pass

def handle_static_type_error(error:StaticTypeError, srcdata:{'filename':str, 'src':str}, exit=True):
    print('\nStatic type error:', file=sys.stderr)
    if error.node:
        print('  File "{}", line {}'.format(srcdata.filename, error.node.lineno), file=sys.stderr)
        print('   ', srcdata.src.split('\n')[error.node.lineno-1], file=sys.stderr)
        print('   ', ' ' * error.node.col_offset + '^', file=sys.stderr)
    else:
        print('  File "{}", line 1'.format(srcdata.filename), file=sys.stderr)
    print(error.msg, file=sys.stderr)
    print(file=sys.stderr)
    if exit:
        quit()

def handle_malformed_type_error(error:StaticTypeError, srcdata:{'filename':str, 'src':str}, exit=True):
    print('\nMalformed type annotation:', file=sys.stderr)
    if error.node:
        print('  File "{}", line {}'.format(srcdata.filename, error.node.lineno), file=sys.stderr)
        print('   ', srcdata.src.split('\n')[error.node.lineno-1], file=sys.stderr)
        print('   ', ' ' * error.node.col_offset + '^', file=sys.stderr)
    else:
        print('  File "{}", line 1'.format(srcdata.filename), file=sys.stderr)
    print(error.msg, file=sys.stderr)
    print(file=sys.stderr)
    if exit:
        quit()
