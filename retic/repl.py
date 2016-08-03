#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os, platform, sys, ast, traceback
from . import flags, static, exc

try:
    import readline
except ImportError:
    pass

PSTART = ':>> '
PCONT = '... '
PTYPE = '⊢ ' if os.name != 'nt' else '|-'

def repl_reticulate(pgm, dict, env, semantics):
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
                    static.repl_exec_module(cmodule, srcdata, dict)
                    mod = []
                expr = ast.Expression(body=stmt.value)
                eres = static.repl_eval_module(expr, srcdata, dict)
                if eres is not None:
                    print(eres)
            else:
                mod.append(stmt)
        if mod:
            cmodule = ast.Module(body=mod)
            static.repl_exec_module(cmodule, srcdata, dict)
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
        v, e, tb = sys.exc_info()
        exc.handle_runtime_error(v, e, tb, exit=False)
        return {}

def repl(*, semantics):
    main, _ = static.setup_main_dict(static.srcdata(src='', filename='<string>'))
    static.setup_import_hook(main)

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
            env.update(repl_reticulate(pgm, main, env, semantics))
        else: 
            if multimode or strip.endswith(':') or strip.endswith('\\') or strip.startswith('@'):
                multimode = True
                buf.append(line)
                prompt = PCONT
            else:
                prompt = PSTART
                buf = []
                env.update(repl_reticulate(line, main, env, semantics))
