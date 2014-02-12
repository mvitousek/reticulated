class Function:
    def __init__(self, pos, pos_def, varargs, kw, kwonly):
        pass

def call_typechecks(n, env):
    funty = getfunctiontype
    for arg, param in zip(n.positional, funty.pos + funty.pos_def):
        match(arg, param)
    opt_pos = set(funty.kwonly)
    varparams = []
    req_pos = []
    if |n.positional| < |funty.pos|:
        req_pos = set(funty.pos[|n.positional|:])
        opt_pos |= set(funty.pos_def)
    elif |n.positional| < |funty.pos| + |funty.pos_def|:
        opt_pos |= set(funty.pos_def[(|n.positional| - |funty.pos|)])
    elif |n.positional| > |funty.pos| + |funty.pos_def|:
        what about starargs
        varparams = n.positional[|funty.pos| + |funty.pos_def|:]

    for kw in n.kwargs:
        if kw in req_pos:
            match(kw, req_pos[kw])
            req_pos.remove(kw)
        elif kw in opt_pos:
            match(kw, opt_pos[kw])
            opt_pos.remove(kw)
        elif funty.kwargs:
            match(kw, funty.kwargs)
        else error()
    if not req_pos and not n.kwargs:
        error()

    for param in varparams:
        if not funty.varargs:
            error()
        else match(param, funty.varargs)

    
