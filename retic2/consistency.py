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
            elif len(args) != len(fty.froms.types):
                index = min(len(fty.froms.types), len(args)-1)
                return False, exc.StaticTypeError(args[index] if index >= 0 else fn, 'Too {} arguments, {} {} expected'.format('many' if len(args) > len(fty.froms.types) else 'few',
                                                                                                                                        len(fty.froms.types), 
                                                                                                                                        'was' if len(fty.froms.types) == 1 else 'were'))
            else:
                for i, (param, arg) in enumerate(zip(fty.froms.types, args)):
                    if not assignable(param, arg.retic_type):
                        return False, exc.StaticTypeError(arg, 'Argument {} has type {}, but a value of type {} was expected'.format(i, arg.retic_type, param))
                return fty.to, None
        else:
            raise exc.UnimplementedException()
    elif isinstance(fty, retic_ast.Bot):
        return retic_ast.Bot(), None
    else:
        return False, exc.StaticTypeError(fn, 'Cannot apply value of type {}'.format(fty))

def consistent(t1: retic_ast.Type, t2: retic_ast.Type):
    ## Are two types consistent (i.e. the same up to Dyn)?
    ## This is the semantic relation usually written as 
    ##               _______
    ##               T1 ~ T2
    if isinstance(t1, retic_ast.Dyn) or isinstance(t2, retic_ast.Dyn):
        return True
    elif isinstance(t1, retic_ast.Bot) or isinstance(t2, retic_ast.Bot):
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
# Primitive subtypes:
# bool <: int <: float
def assignable(into: retic_ast.Type, orig: retic_ast.Type):
    if consistent(into, orig):
        return True
    elif isinstance(into, retic_ast.Float):
        return any(isinstance(orig, ty) for ty in [retic_ast.Float, retic_ast.Int, retic_ast.Bool])
    elif isinstance(into, retic_ast.Int):
        return any(isinstance(orig, ty) for ty in [retic_ast.Int, retic_ast.Bool])
    else: return False

# Member assignabilty sees if the members of the RHS can be written into the LHS.
def member_assignable(l: retic_ast.Type, r: retic_ast.Type):
    itr = iterable_type(r)
    if itr:
        return assignable(l, itr)
    else: return False

# Instance assignability holds if an instance of the type on the RHS can be written into the LHS.
def instance_assignable(l: retic_ast.Type, r: retic_ast.Type):
    instr = instance_type(r)
    if instr:
        return assignable(l, instr)
    else: return False

# Iterable type gets the type of the resulting values when the type is iterated over,
# or False if the type cannot be iterated over
def iterable_type(ty: retic_ast.Type):
    if isinstance(ty, retic_ast.Dyn):
        return retic_ast.Dyn()
    elif isinstance(ty, retic_ast.List):
        return ty.elts
    else: 
        return False

# Instance type gets the type of an instantiation of the type
# or False if the type cannot be instantiated
def instance_type(ty: retic_ast.Type):
    if isinstance(ty, retic_ast.Dyn):
        return retic_ast.Dyn()
    else: 
        return False


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
        if isinstance(typ, retic_ast.Bot):
            continue
        elif isinstance(typ, retic_ast.Primitive) and isinstance(ty, retic_ast.Primitive) and \
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
            

def apply_binop(op: ast.operator, l:retic_ast.Type, r:retic_ast.Type):
    if isinstance(l, retic_ast.Dyn):
        return retic_ast.Dyn()
    elif (not isinstance(op, ast.Mod) or not isinstance(l, retic_ast.Str))\
         and isinstance(r, retic_ast.Dyn): # If LHS is a string and op is %, then we def have a string
        return retic_ast.Dyn()
    if isinstance(op, ast.Add):
        if assignable(retic_ast.Int(), l) and assignable(retic_ast.Int(), r):
            return retic_ast.Int()
        elif assignable(retic_ast.Float(), l) and assignable(retic_ast.Float(), r):
            return retic_ast.Float()
        elif assignable(retic_ast.Str(), l) and assignable(retic_ast.Str(), r):
            return retic_ast.Str()
        elif assignable(retic_ast.List(retic_ast.Dyn()), l) and assignable(retic_ast.List(retic_ast.Dyn()), r):
            return join(l, r)
        else: 
            return False
    elif isinstance(op, ast.Sub) or isinstance(op, ast.Div) or isinstance(op, ast.Pow): # These ones can take floats
        if assignable(retic_ast.Int(), l) and assignable(retic_ast.Int(), r):
            return retic_ast.Int()
        elif assignable(retic_ast.Float(), l) and assignable(retic_ast.Float(), r):
            return retic_ast.Float()
        else: 
            return False
    elif isinstance(op, ast.FloorDiv): # Takes floats, but always return int
        if assignable(retic_ast.Float(), l) and assignable(retic_ast.Float(), r):
            return retic_ast.Int()
        else: 
            return False
    elif isinstance(op, ast.LShift) or isinstance(op, ast.RShift) or \
         isinstance(op, ast.BitOr) or isinstance(op, ast.BitXor) or isinstance(op, ast.BitAnd): # These ones cant
        if assignable(retic_ast.Int(), l) and assignable(retic_ast.Int(), r):
            return retic_ast.Int()
        else: 
            return False
    elif isinstance(op, ast.Mod): # Can take floats
        if assignable(retic_ast.Int(), l) and assignable(retic_ast.Int(), r):
            return retic_ast.Int()
        elif assignable(retic_ast.Float(), l) and assignable(retic_ast.Float(), r):
            return retic_ast.Float()
        elif assignable(retic_ast.Str(), l):
            return retic_ast.Str()
        else: 
            return False
    elif isinstance(op, ast.Mult): # Can take floats
        if assignable(retic_ast.Int(), l) and assignable(retic_ast.Int(), r):
            return retic_ast.Int()
        elif assignable(retic_ast.Float(), l) and assignable(retic_ast.Float(), r):
            return retic_ast.Float()
        if assignable(retic_ast.Str(), l) and assignable(retic_ast.Int(), r):
            return retic_ast.Str()
        if assignable(retic_ast.Int(), l) and assignable(retic_ast.Str(), r):
            return retic_ast.Str()
        else: 
            return False
    else:
        raise InternalReticulatedError(op)

def apply_unop(op: ast.unaryop, o:retic_ast.Type):
    if isinstance(o, retic_ast.Dyn):
        return retic_ast.Dyn()
    elif isinstance(op, ast.Not):
        return retic_ast.Bool()
    elif isinstance(op, ast.Invert):
        if assignable(retic_ast.Int(), o): #no float
            return retic_ast.Int()
        else:
            return False
    elif isinstance(op, ast.UAdd) or isinstance(op, ast.USub):
        if assignable(retic_ast.Int(), o): #yes float
            return retic_ast.Int()
        elif assignable(retic_ast.Float(), o): 
            return retic_ast.Int()
        else:
            return False
