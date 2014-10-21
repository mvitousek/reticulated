from __future__ import print_function

import astor.codegen
import sys, ast, flags

def unparse(ast: ast.Module, file=sys.stdout):
    if flags.SEMANTICS == 'NOOP' and flags.INLINE_DUMMY_DEFS:
        ast = insert_dummy_defs(ast)
    else: 
        ast = insert_import(ast)
    print(astor.codegen.to_source(ast), file=file)
    
def insert_import(st: ast.Module)->ast.Module:
    if len(st.body) > 0 and \
       isinstance(st.body[0], ast.ImportFrom) and \
       st.body[0].module == '__future__':
        ins = 1
    else:
        ins = 0

    body = st.body[:]
    if flags.SEMANTICS != 'NOOP':
        body.insert(ins, ast.ImportFrom(level=0, module='typing', names=[ast.alias(name='*', asname=None)]))
        body.insert(ins, ast.ImportFrom(level=0, module=flags.SEM_NAMES[flags.SEMANTICS], names=[ast.alias(name='*', asname=None)]))
        body.insert(ins, ast.ImportFrom(level=0, module='runtime', names=[ast.alias(name='*', asname=None)]))
    else:
        body.insert(ins, ast.ImportFrom(level=0, module='noop', names=[ast.alias(name='*', asname=None)]))
        body.insert(ins, ast.ImportFrom(level=0, module='dummy_types', names=[ast.alias(name='*', asname=None)]))
        
    return ast.Module(body=body)

def insert_dummy_defs(st: ast.Module)-> ast.Module:
    if len(st.body) > 0 and \
       isinstance(st.body[0], ast.ImportFrom) and \
       st.body[0].module == '__future__':
        ins = 1
    else:
        ins = 0
    
    with open('dummy_types.py', 'r') as dt,\
         open('noop.py', 'r') as np:
        dt_st = ast.parse(dt.read())
        np_st = ast.parse(np.read())
        body = st.body[:ins] + dt_st.body + np_st.body + st.body[ins:]
        return ast.Module(body=body)

