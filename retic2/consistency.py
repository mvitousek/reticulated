## This module defines the consistency relation on Types as well as
## lots of other relations that use consistency.

from . import typing, retic_ast, exc
import ast

def apply(fn: ast.expr, fty: retic_ast.Type, args: typing.List[ast.expr], keywords: typing.List[ast.keyword], starargs, kwargs):
    ## Takes a function, the function's type, and the arguments to the
    ## function, and see if the arguments can validly be passed into
    ## the function based on the function's type. If the answer is
    ## yes, then a tuple of the return type of the function
    ## application and None is returned. If the answer is no, then a
    ## tuple of False and a exc.StaticTypeError to be raised is
    ## returned.

    ## The function itself, fn, is only used to point out an error
    ## location if certain kinds of static type errors are raised.
    if isinstance(fty, retic_ast.Dyn):
        return retic_ast.Dyn(), None
    elif isinstance(fty, retic_ast.Function):
        if isinstance(fty.froms, retic_ast.ArbAT):
            return fty.to, None
        elif isinstance(fty.froms, retic_ast.PosAT):
            if kwargs:
                return False, exc.StaticTypeError(kwargs, 'Cannot pass keyword arguments into a function of type {}'.format(fty))
            elif keywords:
                return False, exc.StaticTypeError(keywords[0].value, 'Cannot pass keywords into a function of type {}'.format(fty))
            elif starargs:
                if not consistent(retic_ast.List(join(*fty.froms.types[len(args):])), starargs.retic_type):
                    ty = starargs.retic_type.elts if isinstance(starargs.retic_type, retic_ast.List) else retic_ast.Dyn()
                    return False, exc.StaticTypeError(starargs, 'Stararg elements have combined type {},' +\
                                                      ' which does not the combined type {} for the remaining parameters'.format(ty, join(*fty.froms.types[len(args):])))
                elif len(args) > len(fty.froms.types):
                    return False, exc.StaticTypeError(args[len(fty.froms.types)], 'Too many arguments, {} {} expected'.format(len(fty.froms.types), 
                                                                                                                              'was' if len(fty.froms.types) == 1 else 'were'))
                else:
                    for i, (param, arg) in enumerate(zip(fty.froms.types, args)):
                        if not assignable(param, arg.retic_type):
                            return False, exc.StaticTypeError(arg, 'Argument {} has type {}, but a value of type {} was expected'.format(i, arg.retic_type, param))
                    return fty.to, None
            elif len(args) > len(fty.froms.types):
                return False, exc.StaticTypeError(args[len(fty.froms.types)], 'Too many arguments, {} {} expected'.format(len(fty.froms.types), 
                                                                                                                          'was' if len(fty.froms.types) == 1 else 'were'))
            elif len(args) < len(fty.froms.types):
                return False, exc.StaticTypeError(args[len(fty.froms.types)], 'Too few arguments, {} {} expected'.format(len(fty.froms.types), 
                                                                                                                          'was' if len(fty.froms.types) == 1 else 'were'))
            else:
                for i, (param, arg) in enumerate(zip(fty.froms.types, args)):
                    if not assignable(param, arg.retic_type):
                        return False, exc.StaticTypeError(arg, 'Argument {} has type {}, but a value of type {} was expected'.format(i, arg.retic_type, param))
                return fty.to, None
        else:
            raise exc.UnimplementedException()
    else:
        return False, exc.StaticTypeError(fn, 'Cannot apply value of type {}'.format(fty))

def consistent(t1: retic_ast.Type, t2: retic_ast.Type):
    ## Are two types consistent (i.e. the same up to Dyn)?
    ## This is the semantic relation usually written as 
    ##               _______
    ##               T1 ~ T2
    if isinstance(t1, retic_ast.Dyn) or isinstance(t2, retic_ast.Dyn):
        return True
    elif isinstance(t1, retic_ast.Primitive):
        return t1.__class__ is t2.__class__
    elif isinstance(t1, retic_ast.List):
        return isinstance(t2, retic_ast.List) and \
            consistent(t1.elts, t2.elts)
    elif isinstance(t1, retic_ast.Function):
        return isinstance(t2, retic_ast.Function) and \
            param_consistent(t1.froms, t2.froms) and\
            consistent(t1.to, t2.to)
    else: raise exc.UnimplementedException(t1, t2)

def param_consistent(t1: retic_ast.ArgTypes, t2: retic_ast.ArgTypes):
    ## Consistency, but for parameters
    if isinstance(t1, retic_ast.ArbAT) or isinstance(t2, retic_ast.ArbAT):
        return True
    elif isinstance(t1, retic_ast.PosAT):
        return isinstance(t2, retic_ast.PosAT) and \
            all(consistent(t1a, t2a) for t1a, t2a in zip(t1.types, t2.types))
    else: raise exc.UnimplementedException

# Assignability takes two arguments and sees if the second can be
# passed into the first. This is also called subtype consistency. NOTE
# THAT THIS RELATION IS REVERSED
# ________
# T2 <~ T1
#
# Right now, our types don't have any kind of subtyping, so
# assignability is just consistency.
assignable = consistent

# Join finds an upper bound (hopefully the lowest upper bound) of a
# set of types with respect to precision/naive subtyping, and goes "up
# towards Dyn". That is, every type in 'tys' should be consistent with
# the return value of this function.
def join(*tys):
    if len(tys) == 0:
        return retic_ast.Dyn()
    ty = tys[0]
    if isinstance(ty, retic_ast.Dyn):
        return ty
    for typ in tys[1:]:
        if isinstance(typ, retic_ast.Primitive) and isinstance(ty, retic_ast.Primitive) and \
           ty.__class__ is typ.__class__:
            continue
        elif isinstance(typ, retic_ast.Function) and isinstance(ty, retic_ast.Function):
            ty = retic_ast.Function(param_join(ty.froms, typ.froms),
                                    join(ty.to, typ.to))
        elif isinstance(typ, retic_ast.List) and isinstance(ty, retic_ast.List):
            ty = retic_ast.List(join(typ.elts, ty.elts))
        else: return retic_ast.Dyn()
    return ty

# Join but for parameters
def param_join(p1, p2):
    if isinstance(p1, retic_ast.ArbAT) or isinstance(p2, retic_ast.ArbAT):
        return retic_ast.ArbAT()
    elif isinstance(p1, retic_ast.PosAT) and isinstance(p2, retic_ast.PosAT):
        if len(p1.types) == len(p2.types):
            return retic_ast.PosAT([join(t1, t2) for t1, t2 in zip(p1.types, p2.types)])
        else:
            return retic_ast.ArbAT()
    else:
        return retic_ast.ArbAT()
            
