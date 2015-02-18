#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import print_function
import traceback, ast, __main__, sys, os, platform
from . import typecheck, typing, flags, assignee_visitor, exc, utils, runtime, static
from .importer import make_importer

try:
    import readline
except ImportError:
    pass

if flags.PY_VERSION == 3:
    from .exec3 import _exec
    input_fn = input
else: 
    from .exec2 import _exec
    input_fn = raw_input

PSTART = ':>> '
PCONT = '... '
PTYPE = '⊢ ' if os.name != 'nt' else '|-'

def repl_reticulate(pgm, context, env, static):
    try:
        av = assignee_visitor.AssigneeVisitor()

        py_ast = ast.parse(pgm)

        try:
            typed_ast, env = static.typecheck_module(py_ast, '<string>', 0, env)
        except exc.StaticTypeError as e:
            utils.handle_static_type_error(e, exit=False)
            return


        ids = av.preorder(typed_ast)
        for id in ids:
            print(PTYPE + ' %s : %s' % (id, env[typing.Var(id)]))

        mod = []
        for stmt in typed_ast.body:
            if isinstance(stmt, ast.Expr):
                if mod:
                    cmodule = ast.Module(body=mod)
                    ccode = compile(cmodule, '<string>', 'exec')
                    _exec(ccode, context)
                expr = ast.Expression(body=stmt.value)
                ecode = compile(expr, '<string>', 'eval')
                eres = eval(ecode, context)
                if eres is not None:
                    print(eres)
            else:
                mod.append(stmt)
        if mod:
            cmodule = ast.Module(body=mod)
            ccode = compile(cmodule, '<string>', 'exec')
            _exec(ccode, context)    
    except SystemExit:
        print()
        exit()    
    except KeyboardInterrupt:
        print()
        exit()
    except EOFError:
        print()
        exit()
    except Exception:
        utils.handle_runtime_error(exit=False)
    except exc.RuntimeTypeError:
        utils.handle_runtime_error(exit=False)
    return env

def repl():
    print('Welcome to Reticulated Python!')
    print('[version {}/{}, running on {} {}.{}.{}]'.format(flags.VERSION, flags.SEMANTICS, 
                                              platform.python_implementation(),
                                              sys.version_info.major, sys.version_info.minor,
                                              sys.version_info.micro))
    buf = []
    prompt = PSTART
    multimode = False    
    env = {}
    if flags.SEMANTICS == 'TRANS':
        from . import transient as cast_semantics
    elif flags.SEMANTICS == 'MONO':
        from . import monotonic as cast_semantics
    elif flags.SEMANTICS == 'GUARDED':
        from . import guarded as cast_semantics
    else:
        assert False, 'Unknown semantics ' + flags.SEMANTICS

    type_system = static.StaticTypeSystem()

    omain = __main__.__dict__.copy()

    code_context = {}
    code_context.update(typing.__dict__)
    if not flags.DRY_RUN:
        code_context.update(cast_semantics.__dict__)
        code_context.update(runtime.__dict__)
        
    __main__.__dict__.update(code_context)
    __main__.__dict__.update(omain)
    __main__.__file__ = '<string>'

    if flags.TYPECHECK_IMPORTS:
        sys.path.insert(0, '')
        importer = make_importer(code_context, type_system)
        if flags.TYPECHECK_LIBRARY:
            sys.path_importer_cache.clear()
        sys.path_hooks.insert(0, importer)

    while True:
        try:
            line = input_fn(prompt)
        except KeyboardInterrupt:
            print()
            exit()
        strip = line.strip()
        if line == '' and multimode:
            pgm = '\n'.join(buf)
            buf = []
            prompt = PSTART
            multimode = False
            env = repl_reticulate(pgm, __main__.__dict__, env, type_system)
        else: 
            if multimode or strip.endswith(':') or strip.endswith('\\') or strip.startswith('@'):
                multimode = True
                buf.append(line)
                prompt = PCONT
            else:
                prompt = PSTART
                buf = []
                env = repl_reticulate(line, __main__.__dict__, env, type_system)
