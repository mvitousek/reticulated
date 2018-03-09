from . import ctypes
from .. import argspec, exc
from .constraints import *
import ast


class ApplyFail(Exception): pass

def apply_args(fn, at, rt, args, keywords, starargs, kwargs):
    ## This aux function is used to check whether a subset of the
    ## expected positional arguments are satisfied by the call's
    ## args. It doesn't do any reasoning about satisfying the expected
    ## number of args. It returns the same things that the overall
    ## function returns, so it can be passed directly to return
    def check_pos(positionals, st):
        for i, (param, arg) in enumerate(zip(positionals, args)):
            st |= {STC(arg.retic_ctype, param)}
        return rt, st

    def types_from_named(named):
        return [t for n, t in named]

    allargs = args + [kwd.value for kwd in keywords] + ([starargs] if starargs else []) + ([kwargs] if kwargs else [])
    
    if isinstance(at, ctypes.SpecCAT):
        st = set()
        binding = argspec.capply(fn, at.spec, args, keywords, starargs, kwargs)
        if isinstance(binding, exc.StaticTypeError):
            raise ApplyFail()

        for param in binding.arguments:
            arg = binding.arguments[param]
            desc, paramty = argspec.paramty(param, at.spec)
            if isinstance(arg, dict):
                for key in arg:
                    st |= {STC(arg[key].type, paramty)}
            elif isinstance(arg, argspec.argty):
                st |= {STC(arg.type, paramty)}
            elif isinstance(arg, tuple):
                for elt in arg:
                    st |= {STC(elt.type, paramty)}
            else: raise Exception()
        return rt, st

    elif isinstance(at, ctypes.ArbCAT):
        return rt, {STC(arg.retic_ctype, ctypes.CDyn()) for arg in allargs}
    elif isinstance(at, ctypes.ReadOnlyArbCAT):
        return rt, set()

    # Logic for positional arguments
    elif isinstance(at, ctypes.PosCAT):
        if starargs:
            st = {EltSTC(starargs.retic_ctype, atty) for atty in at.types[len(args):]}
            return check_pos(at.types, st)

        if len(at.types) == len(args):
            return check_pos(at.types, set())
        else:
            raise ApplyFail(at.types, args)

def instance_type(cls):
    return ctypes.CInstance(cls.name)

def apply(fn: ast.expr, fty, args, keywords, starargs, kwargs, ctbl):
    if isinstance(fty, ctypes.CFunction):
        return apply_args(fn, fty.froms, fty.to, args, keywords, starargs, kwargs)
    elif isinstance(fty, ctypes.CClass):
        to = instance_type(fty)
        st = set()
        try:
            init = ctbl[fty.name].lookup('__init__', ctbl)
        except KeyError:
            raise exc.InternalReticulatedError('class that doesn\'t support init?')
        
            
        ty, stp = apply(fn, init.bind(), args, keywords, starargs, kwargs, ctbl)
        st |= stp
        return to, st
    elif isinstance(fty, ctypes.CInstance):
        st = set()
        
        try:
            call = ctbl[fty.instanceof].instance_lookup('__call__', ctbl)
        except KeyError:
            return CDyn(), st
        
        ty, stp = apply(fn, call, args, keywords, starargs, kwargs, ctbl)
        st |= stp
        return ty, st
    elif isinstance(fty, ctypes.CIntersection):
        for t in fty.types:
            try:
                return apply(fn, t, args, keywords, starargs, kwargs, ctbl)
            except ApplyFail:
                continue
    else:
        raise Exception(fty)


def setter_curry(n, methodty, setty):
    def curry_types(into, expect):
        return expect, {STC(setty, into)}

    if isinstance(methodty, ctypes.CFunction):
        if isinstance(methodty.froms, ctypes.ArbCAT):
            return retic_ast.Dyn(), set()
        elif isinstance(methodty.froms, ctypes.PosCAT):
            if len(methodty.froms.types) != 2:
                raise exc.InternalReticulatedError()
            else: return curry_types(methodty.froms.types[0], methodty.froms.types[1])
        # elif isinstance(methodty.froms, retic_ast.NamedAT):
        #     if len(methodty.froms.bindings) != 2:
        #         raise exc.InternalReticulatedError()
        #     else: return curry_types(methodty.froms.bindings[0][1], methodty.froms.bindings[1][1])
        # elif isinstance(methodty.froms, retic_ast.ApproxNamedAT):
        #     if len(methodty.froms.bindings) > 2:
        #         raise exc.InternalReticulatedError()
        #     return curry_types(methodty.froms.bindings[0][1] if len(methodty.froms.bindings) > 0 else Dyn(), 
        #                        methodty.froms.bindings[1][1] if len(methodty.froms.bindings) > 0 else Dyn())
        else: raise exc.InternalReticulatedError()
    else:
        raise exc.StaticTypeError(n, 'Setter method of has type {}; either Any or a function type was expected'.format(methodty))

# Iterable type gets the type of the resulting values when the type is iterated over,
# or False if the type cannot be iterated over
def iterable_type(ty: ctypes.CType):
    if isinstance(ty, ctypes.CDyn):
        return ctypes.CDyn(), set()
    elif isinstance(ty, ctypes.CSubscriptable):
        return ty.elts, set()
    elif isinstance(ty, ctypes.CStr):
        return ctypes.CStr(), set()
    elif isinstance(ty, ctypes.CList):
        return ty.elts, set()
    elif isinstance(ty, ctypes.CSet):
        return ty.elts, set()
    elif isinstance(ty, ctypes.CDict):
        return ty.keys, set()
    elif isinstance(ty, ctypes.CHTuple):
        return ty.elts, set()
    else: 
        raise Exception(ty)
