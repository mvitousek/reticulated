from . import retic_ast, typeparser, exc
import inspect
from collections import namedtuple


    

def csignature(args, typeof, cxname):
    def cparse_posargs():
        params = []
        defaults = [inspect.Parameter.empty] * (len(args.args) - len(args.defaults)) + args.defaults
        for deflt, arg in zip(defaults, args.args):
            ty = typeof(arg, cxname, 'arg')
            params.append(inspect.Parameter(arg.arg, inspect.Parameter.POSITIONAL_OR_KEYWORD, default=deflt, annotation=ty))
        return params

    def cparse_vararg():
        if args.vararg:
            ty = typeof(args.vararg, cxname, 'vararg')
            return [inspect.Parameter(args.vararg.arg, inspect.Parameter.VAR_POSITIONAL, default=inspect.Parameter.empty, annotation=ty)]
        else:
            return []

    def cparse_keywords():
        params = []
        kwdefaults = [(d if d else inspect.Parameter.empty) for d in args.kw_defaults]
        for deflt, arg in zip(kwdefaults, args.kwonlyargs):
            ty = typeof(arg, cxname, 'kwoarg')
            params.append(inspect.Parameter(arg.arg, inspect.Parameter.KEYWORD_ONLY, default=deflt, annotation=ty))
        return params

    def cparse_kwargs():
        if args.kwarg:
            ty = typeof(args.kwarg, cxname, 'kwarg')
            return [inspect.Parameter(args.kwarg.arg, inspect.Parameter.VAR_KEYWORD, default=inspect.Parameter.empty, annotation=ty)]
        else:
            return []

    params = cparse_posargs() + cparse_vararg() + cparse_keywords() + cparse_kwargs()
    return inspect.Signature(params)


def signature(args, env):
    def parse_posargs():
        params = []
        defaults = [inspect.Parameter.empty] * (len(args.args) - len(args.defaults)) + args.defaults
        for deflt, arg in zip(defaults, args.args):
            if arg.annotation:
                ty = typeparser.typeparse(arg.annotation, env)
            else:
                ty = retic_ast.Dyn()
            params.append(inspect.Parameter(arg.arg, inspect.Parameter.POSITIONAL_OR_KEYWORD, default=deflt, annotation=ty))
        return params

    def parse_vararg():
        if args.vararg:
            if args.vararg.annotation:
                ty = typeparser.typeparse(args.vararg.annotation, env)
            else:
                ty = retic_ast.Dyn()
            return [inspect.Parameter(args.vararg.arg, inspect.Parameter.VAR_POSITIONAL, default=inspect.Parameter.empty, annotation=ty)]
        else:
            return []

    def parse_keywords():
        params = []
        kwdefaults = [(d if d else inspect.Parameter.empty) for d in args.kw_defaults]
        for deflt, arg in zip(kwdefaults, args.kwonlyargs):
            if arg.annotation:
                ty = typeparser.typeparse(arg.annotation, env)
            else:
                ty = retic_ast.Dyn()
            params.append(inspect.Parameter(arg.arg, inspect.Parameter.KEYWORD_ONLY, default=deflt, annotation=ty))
        return params

    def parse_kwargs():
        if args.kwarg:
            if args.kwarg.annotation:
                ty = typeparser.typeparse(args.kwarg.annotation, env)
            else:
                ty = retic_ast.Dyn()
            return [inspect.Parameter(args.kwarg.arg, inspect.Parameter.VAR_KEYWORD, default=inspect.Parameter.empty, annotation=ty)]
        else:
            return []    

    params = parse_posargs() + parse_vararg() + parse_keywords() + parse_kwargs()
    return inspect.Signature(params)

def paramty(name, spec):
    for param in spec.parameters:
        if param == name:
            return 'Argument', spec.parameters[param].annotation
    raise Exception()

argty = namedtuple('argty', ['arg', 'type'])

def apply(fn, spec, args, keywords, starargs, kwargs):

    postvarargs = False
    postkwargs = False

    appargs = [argty(arg, arg.retic_type) for arg in args]

    if starargs is not None:
        if isinstance(starargs.retic_type, retic_ast.Tuple):
            appargs += [argty(starargs, ty) for ty in starargs.retic_type.elts]
        elif isinstance(starargs.retic_type, retic_ast.List):
            postvarargs = starargs.retic_type.elts
        elif isinstance(starargs.retic_type, retic_ast.HTuple):
            postvarargs = starargs.retic_type.elts
        elif isinstance(starargs.retic_type, retic_ast.Dyn):
            appargs += [argty(starargs, retic_ast.Dyn())] * (len([spec.parameters[param] for param in spec.parameters if \
                                                                  spec.parameters[param].kind == inspect.Parameter.POSITIONAL_ONLY or\
                                                                  spec.parameters[param].kind == inspect.Parameter.POSITIONAL_OR_KEYWORD]) -\
                                                             len(appargs))
        else:
            # This is called by consistency.apply_args, which can't directly raise static type errors, so we return rather than raise.
            return exc.StaticTypeError(starargs, 'Vararg has type {}, but a list or tuple was expected.'.format(starargs.retic_type))

    appkws = {arg.arg: argty(arg.value, arg.value.retic_type) for arg in keywords}

    if kwargs is not None:
        if isinstance(kwargs.retic_type, retic_ast.Dyn):
            remaining = [spec.parameters[param] for param in spec.parameters if spec.parameters[param].kind == inspect.Parameter.POSITIONAL_ONLY or\
                         spec.parameters[param].kind == inspect.Parameter.POSITIONAL_OR_KEYWORD][len(appargs):] + \
                        [spec.parameters[param] for param in spec.parameters if spec.parameters[param].kind == inspect.KEYWORD_ONLY]
            remaining = [param for param in remaining if param.name not in appkws]
            appkws.update({param.name: argty(kwargs, retic_ast.Dyn()) for param in remaining})
        elif isinstance(kwargs.retic_type, retic_ast.Dict):
            postkwargs = kwargs.retic_type.values
        else:
            return exc.StaticTypeError(kwargs, 'Keyword arguments have type {}, but a dictionary was expected.'.format(kwargs.retic_type))

    try:
        ba = spec.bind(*appargs, **appkws)
    except TypeError as te:
        msg = te.args[0]
        if postvarargs:
            msg += ' (Cannot statically check calls with typed *varargs unless the vararg is an explicit tuple'
            if postkwargs:
                msg += ', and cannot statically check calls with typed **keyword arguments)'
            else: msg += ')'
            return None
        elif postkwargs:
            msg += ' (Cannot statically check calls with typed **keyword arguments)'
            return None
        return exc.StaticTypeError(fn, msg)

    if postvarargs:
        specvarargs = [spec.parameters[param] for param in spec.parameters if spec.parameters[param].kind == inspect.Parameter.VAR_POSITIONAL]
        if len(specvarargs) == 0:
            return exc.StaticTypeError(starargs, 'Unexpected varargs')
        else:
            specvararg = specvarargs[0] # Signature shouldn't allow more than 1 vararg
            if specvararg.name in ba.arguments:
                ba.arguments[specvararg.name] = ba.arguments[specvararg.name] + (argty(starargs, postvarargs),)
            else:
                ba.arguments[specvararg.name] = (argty(starargs, postvarargs),)
    if postkwargs:
        speckwargs = [spec.parameters[param] for param in spec.parameters if spec.parameters[param].kind == inspect.Parameter.VAR_KEYWORD]
        if len(speckwargs) == 0:
            return exc.StaticTypeError(kwargs, 'Unexpected keyword arguments')
        else:
            speckwarg = speckwargs[0] # Signature shouldn't allow more than 1 kwarg
            if speckwarg.name in ba.arguments:
                ba.arguments[speckwarg.name]['$$nonvalid python token'] = argty(starargs, postkwargs)
            else:
                ba.arguments[speckwarg.name] = {'$$nonvalid python token':argty(starargs, postkwargs)}

    return ba


def capply(fn, spec, args, keywords, starargs, kwargs):

    postvarargs = False
    postkwargs = False

    appargs = [argty(arg, arg.retic_ctype) for arg in args]

    if starargs is not None:
        if isinstance(starargs.retic_ctype, ctypes.CTuple):
            appargs += [argty(starargs, ty) for ty in starargs.retic_ctype.elts]
        elif isinstance(starargs.retic_ctype, ctypes.CList):
            postvarargs = starargs.retic_ctype.elts
        elif isinstance(starargs.retic_ctype, ctypes.CHTuple):
            postvarargs = starargs.retic_ctype.elts
        elif isinstance(starargs.retic_ctype, ctypes.CDyn):
            appargs += [argty(starargs, ctypes.CDyn())] * (len([spec.parameters[param] for param in spec.parameters if \
                                                                  spec.parameters[param].kind == inspect.Parameter.POSITIONAL_ONLY or\
                                                                  spec.parameters[param].kind == inspect.Parameter.POSITIONAL_OR_KEYWORD]) -\
                                                             len(appargs))
        else:
            # This is called by consistency.apply_args, which can't directly raise static type errors, so we return rather than raise.
            return exc.StaticTypeError(starargs, 'Vararg has type {}, but a list or tuple was expected.'.format(starargs.retic_ctype))

    appkws = {arg.arg: argty(arg.value, arg.value.retic_ctype) for arg in keywords}

    if kwargs is not None:
        if isinstance(kwargs.retic_ctype, ctypes.CDyn):
            remaining = [spec.parameters[param] for param in spec.parameters if spec.parameters[param].kind == inspect.Parameter.POSITIONAL_ONLY or\
                         spec.parameters[param].kind == inspect.Parameter.POSITIONAL_OR_KEYWORD][len(appargs):] + \
                        [spec.parameters[param] for param in spec.parameters if spec.parameters[param].kind == inspect.KEYWORD_ONLY]
            remaining = [param for param in remaining if param.name not in appkws]
            appkws.update({param.name: argty(kwargs, ctypes.CDyn()) for param in remaining})
        elif isinstance(kwargs.retic_ctype, ctypes.CDict):
            postkwargs = kwargs.retic_ctype.values
        else:
            return exc.StaticTypeError(kwargs, 'Keyword arguments have type {}, but a dictionary was expected.'.format(kwargs.retic_ctype))

    try:
        ba = spec.bind(*appargs, **appkws)
    except TypeError as te:
        msg = te.args[0]
        if postvarargs:
            msg += ' (Cannot statically check calls with typed *varargs unless the vararg is an explicit tuple'
            if postkwargs:
                msg += ', and cannot statically check calls with typed **keyword arguments)'
            else: msg += ')'
        elif postkwargs:
            msg += ' (Cannot statically check calls with typed **keyword arguments)'
        return exc.StaticTypeError(fn, msg)

    if postvarargs:
        specvarargs = [spec.parameters[param] for param in spec.parameters if spec.parameters[param].kind == inspect.Parameter.VAR_POSITIONAL]
        if len(specvarargs) == 0:
            return exc.StaticTypeError(starargs, 'Unexpected varargs')
        else:
            specvararg = specvarargs[0] # Signature shouldn't allow more than 1 vararg
            if specvararg.name in ba.arguments:
                ba.arguments[specvararg.name] = ba.arguments[specvararg.name] + (argty(starargs, postvarargs),)
            else:
                ba.arguments[specvararg.name] = (argty(starargs, postvarargs),)
    if postkwargs:
        speckwargs = [spec.parameters[param] for param in spec.parameters if spec.parameters[param].kind == inspect.Parameter.VAR_KEYWORD]
        if len(speckwargs) == 0:
            return exc.StaticTypeError(kwargs, 'Unexpected keyword arguments')
        else:
            speckwarg = speckwargs[0] # Signature shouldn't allow more than 1 kwarg
            if speckwarg.name in ba.arguments:
                ba.arguments[speckwarg.name]['$$nonvalid python token'] = argty(starargs, postkwargs)
            else:
                ba.arguments[speckwarg.name] = {'$$nonvalid python token':argty(starargs, postkwargs)}

    return ba

order = [inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD, inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.KEYWORD_ONLY, inspect.Parameter.VAR_KEYWORD]

def padjoin(spec1, spec2):
    ret = []
    j = 0
    for i in range(len(list(spec1.parameters))):
        ip = spec1.parameters[list(spec1.parameters)[i]]
        if j >= len(list(spec2.parameters)):
            ret.append((ip, None))
            continue
        jp = spec2.parameters[list(spec2.parameters)[j]]
        if ip.kind == jp.kind:
            ret.append((ip, jp))
            j += 1
        elif order.index(ip.kind) < order.index(jp.kind):
            ret.append((ip, None))
        else: 
            while order.index(ip.kind) > order.index(jp.kind) and j < len(list(spec2.parameters)):
                jp = spec2.parameters[list(spec2.parameters)[j]]
                ret.append((None, jp))
                j += 1
    return ret
                
def params(sig):
    keys = list(sig.parameters)
    return [sig.parameters[key] for key in keys]

def str(sig):
    def pfx(kind, dflt):
        p = ''
        if dflt is not inspect.Parameter.empty:
            p = '?'

        if kind == inspect.Parameter.VAR_POSITIONAL:
            p += '*'
        elif kind == inspect.Parameter.VAR_KEYWORD:
            p += '**'
        return p
    kwo = False
    fst = True
    st = ''
    for s in list(sig.parameters):
        if not fst:
            st += ', '
        fst = False
        a = sig.parameters[s]
        if a.kind == inspect.Parameter.KEYWORD_ONLY and not kwo:
            kwo = True
            st += ', *'
        elif a.kind == inspect.Parameter.VAR_POSITIONAL:
            kwo = True

        st += '{}{}:{}'.format(pfx(a.kind, a.default), s, a.annotation)
    return '[' + st + ']'
