#!/usr/bin/python3

import retic, traceback, ast, typecheck, typing, runtime, __main__, flags, assignee_visitor

PSTART = '>>> '
PCONT = '... '

def repl_reticulate(pgm, context):
    av = assignee_visitor.AssigneeVisitor()

    py_ast = ast.parse(pgm)
    
    checker = typecheck.Typechecker()
    typed_ast, env = checker.typecheck(py_ast, '<string>', 0)

    ids = av.preorder(typed_ast)
    for id in ids:
        print('⊢ %s : %s' % (id, env[typing.Var(id)]))

    mod = []
    for stmt in typed_ast.body:
        if isinstance(stmt, ast.Expr):
            if mod:
                cmodule = ast.Module(body=mod)
                ccode = compile(cmodule, '<string>', 'exec')
                exec(ccode, context)
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
        exec(ccode, context)
    

def repl():
    buf = []
    prompt = PSTART
    multimode = False    

    if flags.SEMANTICS == 'CAC':
        import cast_as_check as cast_semantics
    elif flags.SEMANTICS == 'MONO':
        import monotonic as cast_semantics
    elif flags.SEMANTICS == 'GUARDED':
        import guarded as cast_semantics
    else:
        assert False, 'Unknown semantics ' + flags.SEMANTICS

    code_context = {}
    code_context.update(typing.__dict__)
    if not flags.DRY_RUN:
        code_context.update(cast_semantics.__dict__)
        code_context.update(runtime.__dict__)
    code_context.update(__main__.__dict__)

    while True:
        line = input(prompt)
        if line == '' and multimode:
            pgm = '\n'.join(buf)
            buf = []
            prompt = PSTART
            multimode = False
            try:
                repl_reticulate(pgm, code_context)
            except:
                traceback.print_exc()
        else: 
            if multimode or line.strip().endswith(':') or line.strip().endswith('\\'):
                multimode = True
                buf.append(line)
                prompt = PCONT
            else:
                prompt = PSTART
                buf = []
                try:
                    repl_reticulate(line, code_context)
                except:
                    traceback.print_exc()
                

if __name__ == '__main__':
    print('Welcome to Reticulated Python')
    repl()
