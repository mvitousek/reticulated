#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os, platform, sys, ast, traceback
from . import flags, static

try:
    import readline
except ImportError:
    pass

PSTART = ':>> '
PCONT = '... '
PTYPE = '⊢ ' if os.name != 'nt' else '|-'

def repl_reticulate(pgm, env, semantics):
    try:
        st = ast.parse(pgm)
        srcdata = static.srcdata(src=pgm, filename='<string>')
        st = static.typecheck_module(st, srcdata, env, exit=False)
        
        try:
            tys = st.retic_type
        except AttributeError:
            return {}

        for id in tys.exports:
            print('{} {} : {}'.format(PTYPE, id, tys.exports[id]))

        if semantics == 'TRANS':
            st = static.transient_compile_module(st)
        elif semantics != 'NOOP':
            raise UnimplementedException()

        mod = []
        for stmt in st.body:
            if isinstance(stmt, ast.Expr):
                if mod:
                    cmodule = ast.Module(body=mod)
                    static.exec_module(cmodule, srcdata)
                    mod = []
                expr = ast.Expression(body=stmt.value)
                eres = static.eval_module(expr, srcdata)
                if eres is not None:
                    print(eres)
            else:
                mod.append(stmt)
        if mod:
            cmodule = ast.Module(body=mod)
            static.exec_module(cmodule, srcdata)
        return tys.exports
    except SystemExit:
        print()
        exit()    
    except KeyboardInterrupt:
        print()
        exit()
    except EOFError:
        print()
        exit()
    except BaseException as e:
        traceback.print_exc()
        return {}

def repl(*, semantics):
    print('Welcome to Reticulated Python!')
    print('[version {}/{}, running on {} {}.{}.{}]'.format(flags.RETIC_VERSION, semantics, 
                                                           platform.python_implementation(),
                                                           sys.version_info.major, sys.version_info.minor,
                                                           sys.version_info.micro))
    buf = []
    prompt = PSTART
    multimode = False
    env = {}
    while True:
        try:
            line = input(prompt)
        except KeyboardInterrupt:
            print()
            exit()
        strip = line.strip()
        if line == '' and multimode:
            pgm = '\n'.join(buf)
            buf = []
            prompt = PSTART
            multimode = False
            env = repl_reticulate(pgm, env, semantics)
        else: 
            if multimode or strip.endswith(':') or strip.endswith('\\') or strip.startswith('@'):
                multimode = True
                buf.append(line)
                prompt = PCONT
            else:
                prompt = PSTART
                buf = []
                env = repl_reticulate(line, env, semantics)
