## This module defines the consistency relation on Types as well as
## lots of other relations that use consistency.

import operator
from . import typing, retic_ast, exc, argspec
import ast

import traceback

def consistent(t1: retic_ast.Type, t2: retic_ast.Type):
    if isinstance(t1, retic_ast.Dyn) or isinstance(t2, retic_ast.Dyn):
        return True
    elif isinstance(t1, retic_ast.SingletonInt):
        return isinstance(t2, retic_ast.Int) or isinstance(t2, retic_ast.SingletonInt)
    elif isinstance(t2, retic_ast.SingletonInt):
        return isinstance(t1, retic_ast.Int) or isinstance(t1, retic_ast.SingletonInt)
    elif isinstance(t1, retic_ast.Instance) and isinstance(t2, retic_ast.Void):
        return True
    elif isinstance(t2, retic_ast.Instance) and isinstance(t1, retic_ast.Void):
        return True
    elif isinstance(t1, retic_ast.Primitive):
        return t1.__class__ is t2.__class__
    elif isinstance(t1, retic_ast.List):
        return isinstance(t2, retic_ast.List) and \
            consistent(t1.elts, t2.elts) and \
            consistent(t2.elts, t1.elts)
    elif isinstance(t1, retic_ast.Set):
        return isinstance(t2, retic_ast.Set) and \
            consistent(t1.elts, t2.elts)
    elif isinstance(t1, retic_ast.Dict):
        return isinstance(t2, retic_ast.Dict) and \
            consistent(t1.keys, t2.keys) and \
            consistent(t1.values, t2.values)
    elif isinstance(t1, retic_ast.HTuple):
        return isinstance(t2, retic_ast.HTuple) and \
            consistent(t1.elts, t2.elts)
    elif isinstance(t1, retic_ast.Tuple):
        return isinstance(t2, retic_ast.Tuple) and \
            len(t1.elts) == len(t2.elts) and \
            all(consistent(t1a, t2a) for t1a, t2a in zip(t1.elts, t2.elts))
    elif isinstance(t1, retic_ast.Function):
        return isinstance(t2, retic_ast.Function) and \
            param_consistent(t2.froms, t1.froms) and\
            consistent(t1.to, t2.to)
    elif isinstance(t1, retic_ast.Module):
        # Modules aren't really meant to be interchangable based on
        # their types.
        return isinstance(t2, retic_ast.Module) and \
            t1.exports == t2.exports
    elif isinstance(t1, retic_ast.Class):
        # We've set up class types so that they're unique, I
        # think. This would solve the problem of classes with the same
        # name from different namespaces.
        return t1 is t2
    elif isinstance(t1, retic_ast.Instance):
        return isinstance(t2, retic_ast.Instance) and consistent(t1.instanceof, t2.instanceof)
    elif isinstance(t1, retic_ast.Structural):
        return isinstance(t2, retic_ast.Structural) and \
            all(k in t2.members and consistent(t1.members[k], t2.members[k]) for k in t1.members) and \
            all(k in t1.members for k in t2.members)
    elif isinstance(t1, retic_ast.Union):
        if not isinstance(t2, retic_ast.Union):
            return False
        else:
            return are_consis(t1.alternatives, t2.alternatives)
    elif isinstance(t1, retic_ast.Bot) or isinstance(t2, retic_ast.Bot):
        return True

    else: raise exc.UnimplementedException(t1, t2)


def are_consis(t1_list, t2_list):
    """
    Checks if all types in t1_list have corresponding consistent types
    in t2_list, and that all types in t2_list have corresponding elements
    in t1_list
    Utilizes symetery of consistency relation.
    """
    l1 = len(t1_list)
    l2 = len(t2_list)

    consis_relations = [x[:] for x in [[0]*l2]*l1]

    for i in range(l1):
        got_one=False
        for j in range(l2):
            if consistent(t1_list[i], t2_list[j]):
                consis_relations[i][j] = 1
                got_one = True
        if not got_one: return False

    #DI IDEA
    is_consis=consis_relations[0]
    for r in consis_relations:
         is_consis = list(map(operator.add, is_consis, r))

    return 0 not in is_consis

def apply_args(fn: ast.expr, at: retic_ast.ArgTypes, rt: retic_ast.Type, args: typing.List[ast.expr], keywords: typing.List[ast.keyword], starargs, kwargs):

    ## This aux function is used to check whether a subset of the
    ## expected positional arguments are satisfied by the call's
    ## args. It doesn't do any reasoning about satisfying the expected
    ## number of args. It returns the same things that the overall
    ## function returns, so it can be passed directly to return
    def check_pos(positionals):
        for i, (param, arg) in enumerate(zip(positionals, args)):
            if not assignable(param, arg.retic_type):
                return False, exc.StaticTypeError(arg, 'Argument {} has type {}, but a value of type {} was expected'.format(i, arg.retic_type, param))
        return rt, None

    ## This aux function is used to check whether a subset of the
    ## expected named arguments are satisfied by the call's keyword
    ## args. The permissive option indicates whether an error should
    ## be raised if a keyword is provided that isn't recognized by the
    ## parameters. It returns the same things that the overall
    ## function returns, so it can be passed directly to return
    def check_named(positionals, permissive=False):
        kwds = dict(positionals)
        for kwd in keywords:
            if kwd.arg in kwds:
                if not assignable(kwds[kwd.arg], kwd.value.retic_type):
                    return False, exc.StaticTypeError(arg, 'Keyword argument {} has type {}, but a value of type {} was expected'.format(kwd.arg, kwd.value.retic_type, kwds[kwd.arg]))
            elif not permissive:
                return False, exc.StaticTypeError(arg, 'Unexpected keyword argument {}'.format(kwd.arg))
        return rt, None

    def types_from_named(named):
        return [t for n, t in named]


    if isinstance(at, retic_ast.SpecAT):
        binding = argspec.apply(fn, at.spec, args, keywords, starargs, kwargs)
        if isinstance(binding, exc.StaticTypeError):
            return False, binding

        if binding is None:
            return rt, None

        for param in binding.arguments:
            arg = binding.arguments[param]
            desc, paramty = argspec.paramty(param, at.spec)
            if isinstance(arg, dict):
                for key in arg:
                    if not assignable(paramty, arg[key].type):
                        return False, exc.StaticTypeError(arg[key].arg, '{} has type {}, but a value of type {} was expected'.format(desc, arg[key].type, paramty))
            elif isinstance(arg, argspec.argty):
                if not assignable(paramty, arg.type):
                    return False, exc.StaticTypeError(arg.arg, '{} has type {}, but a value of type {} was expected'.format(desc, arg.type, paramty))
            elif isinstance(arg, tuple):
                for elt in arg:
                    if not assignable(paramty, elt.type):
                        return False, exc.StaticTypeError(elt.arg, '{} has type {}, but a value of type {} was expected'.format(desc, elt.type, paramty))
            else: raise Exception()
        return rt, None


    elif isinstance(at, retic_ast.ArbAT):
        return rt, None

    # Logic for positional arguments
    elif isinstance(at, retic_ast.PosAT):
        if kwargs:
            return False, exc.StaticTypeError(kwargs, 'Cannot pass **keyword arguments into function arguments of type {}'.format(at))
        elif keywords:
            return False, exc.StaticTypeError(keywords[0].value, 'Cannot pass keywords into a function arguments of type {}'.format(at))
        elif starargs:
            if not member_assignable(join(*at.types[len(args):]), starargs.retic_type):
                return False, exc.StaticTypeError(starargs, 'Stararg elements have combined type {},' +\
                                                  ' which does not the combined type {} for the remaining parameters'.format(starargs.retic_type, 
                                                                                                                             join(*at.types[len(args):])))
            elif len(args) > len(at.types):
                return False, exc.StaticTypeError(args[len(at.types)], 'Too many arguments, {} {} expected'.format(len(at.types), 
                                                                                                                          'was' if len(at.types) == 1 else 'were'))
            else:
                return check_pos(at.types)
        elif len(args) != len(at.types):
            index = min(len(at.types), len(args)-1)
            return False, exc.StaticTypeError(args[index] if index >= 0 else fn, 'Too {} arguments, {} {} expected'.format('many' if len(args) > len(at.types) else 'few',
                                                                                                                                    len(at.types), 
                                                                                                                                    'was' if len(at.types) == 1 else 'were'))
        else:
            return check_pos(at.types)

    # # Logic for permissive named arguments
    # elif isinstance(at, retic_ast.ApproxNamedAT):
    #     # Check whether the positional arguments match up
    #     _, posexc = check_pos(types_from_named(at.bindings))
    #     if posexc:
    #         return False, posexc

    #     # Check whether the remaining parameters match the provided keywords
    #     remaining = at.bindings[len(args):] if len(args) <= len(at.bindings) else []
    #     return check_named(remaining, permissive=True)

    # # Logic for strict named arguments
    # elif isinstance(at, retic_ast.NamedAT):
    #     # Check whether the positional arguments match up
    #     _, posexc = check_pos(types_from_named(at.bindings))
    #     if posexc:
    #         return False, posexc

        # Check whether the remaining parameters match the provided keywords
        remaining = at.bindings[len(args):] if len(args) <= len(at.bindings) else []
        _, namedexc = check_named(remaining, permissive=False)
        if namedexc:
            return False, namedexc

        rests = []
        for name, ty in remaining:
            if name not in [kwd.arg for kwd in keywords]:
                rests.append(ty)
        rest_ty = join(*rests)

        if len(args) + len(keywords) > len(at.bindings):
            # Find the first extra argument, whether positional or kw, to point to
            if len(args) > len(at.bindings):
                pointed_to = args[len(at.bindings)]
            else:
                pointed_to = keywords[len(at.bindings) - len(args)].value
            return False, exc.StaticTypeError(pointed_to, 'Too many arguments, {} {} expected'.format(len(at.bindings), 
                                                                                                      'was' if len(at.bindings) == 1 else 'were'))
        if len(args) + len(keywords) < len(at.bindings) and not kwargs and not starargs:
            # Find the last argument, whether positional or kw, to point to
            if keywords:
                pointed_to = keywords[-1].value
            elif args:
                pointed_to = args[-1]
            else: pointed_to = fn
            return False, exc.StaticTypeError(pointed_to, 'Too few arguments, {} {} expected'.format(len(at.bindings), 
                                                                                                     'was' if len(at.bindings) == 1 else 'were'))

        if kwargs:
            kw_vals = retic_ast.Dyn() if isinstance(kwargs.retic_type, retic_ast.Dyn) else kwargs.retic_type.values 
            if not assignable(rest_ty, kw_vals):
                return False, exc.StaticTypeError(kwargs, 'Keyword arg elements have combined type {},' +\
                                                  ' which does not match the combined type {} for the remaining parameters'.format(kw_vals, rest_ty))

        if starargs:
            if not member_assignable(rest_ty, starargs.retic_type):
                return False, exc.StaticTypeError(starargs, 'Stararg elements have combined type {},' +\
                                                  ' which does not match the combined type {} for the remaining parameters'.format(starargs.retic_type, rest_ty))
        return rt, None
    else:
        raise exc.UnimplementedException()

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
        return apply_args(fn, fty.froms, fty.to, args, keywords, starargs, kwargs)
    elif isinstance(fty, retic_ast.Class):
        to = instance_type(fty)
        try:
            init = to['__init__']
        except KeyError:
            raise exc.InternalReticulatedError('class that doesn\'t support init?')
            
        _, err = apply(fn, init, args, keywords, starargs, kwargs)


        if err:
            err.msg = 'Applying __init__ method of class {}: {}'.format(fty.name, err.msg)
            return False, err
        else:
            return to, None
    elif isinstance(fty, retic_ast.Instance):
        try:
            call = fty['__call__']
        except KeyError:
            return False, exc.StaticTypeError(fn, 'Cannot apply value of type {}'.format(fty))
            
        ty, err = apply(fn, call, args, keywords, starargs, kwargs)


        if err:
            err.msg = 'Applying __call__ method of class {}: {}'.format(fty.instanceof.name, err.msg)
            return False, err
        else:
            return ty, None
        
    elif isinstance(fty, retic_ast.Bot):
        return retic_ast.Bot(), None
    else:
        return False, exc.StaticTypeError(fn, 'Cannot apply value of type {}'.format(fty))


# I think that the permissive vs strict arg types should be related
# through subtyping, not consistency. It seems bad to be able to write
# a strict function into a permissive variable. The possible exception
# is the arity of approx things
def param_consistent(t1: retic_ast.ArgTypes, t2: retic_ast.ArgTypes):
    ## Consistency, but for parameters
    if isinstance(t1, retic_ast.ArbAT) or isinstance(t2, retic_ast.ArbAT):
        return True
    elif isinstance(t1, retic_ast.PosAT):
        if isinstance(t2, retic_ast.PosAT): 
            return len(t1.types) == len(t2.types) and \
                all(consistent(t1a, t2a) for t1a, t2a in zip(t1.types, t2.types))
        elif len(t1.types) == 0:
            if isinstance(t2, retic_ast.SpecAT):
                return len(t2.spec.parameters) == 0
            # if isinstance(t2, retic_ast.NamedAT):
            #     return len(t2.bindings) == 0
            else: return False
        else: return False
    elif isinstance(t1, retic_ast.SpecAT):
        if isinstance(t2, retic_ast.SpecAT):
            for k1, k2 in zip(t1.spec.parameters, t2.spec.parameters):
                at1 = t1.spec.parameters[k1]
                at2 = t2.spec.parameters[k2]
                if not (k1 == k2 and at1.kind == at2.kind and consistent(at1.annotation, at2.annotation)):
                    return False
            return len(t1.spec.parameters) == len(t2.spec.parameters) 
        elif len(t1.spec.parameters) == 0:
            if isinstance(t2, retic_ast.PosAT):
                return len(t2.types) == 0
            else: return False
        else: return False
    # elif isinstance(t1, retic_ast.NamedAT):
    #     if isinstance(t2, retic_ast.NamedAT):
    #         return len(t1.bindings) == len(t2.bindings) and \
    #             all(k1 == k2 and consistent(t1a, t2a) for (k1, t1a), (k2, t2a) in zip(t1.bindings, t2.bindings))
    #     elif len(t1.types) == 0:
    #         if isinstance(t2, retic_ast.PosAT):
    #             return len(t2.types) == 0
    #         else: return False
    #     else: return False
    # elif isinstance(t1, retic_ast.ApproxNamedAT):
    #     # We will treat arity of approx ATs as consistency
    #     return isinstance(t2, retic_ast.ApproxNamedAT) and \
    #         all(k1 == k2 and consistent(t1a, t2a) for (k1, t1a), (k2, t2a) in zip(t1.bindings, t2.bindings))
    else: raise exc.UnimplementedException(t1, t2)

# Assignability takes two arguments and sees if the second can be
# passed into the first. This is also called subtype consistency. NOTE
# THAT THIS RELATION IS REVERSED
# ________
# T2 <~ T1
#
# Primitive subtypes:
# bool <: int <: float
#
# I don't think there's a subtyping relation between lists and
# tuples. lists support e.g. the append method, while tuples contain
# more information (length)

def assignable(into: retic_ast.Type, orig: retic_ast.Type)->bool:
    if consistent(orig, into):
        return True

    
    if isinstance(into, retic_ast.Float):
        return any(isinstance(orig, ty) for ty in [retic_ast.Float, retic_ast.Int, retic_ast.Bool, retic_ast.SingletonInt])
    elif isinstance(into, retic_ast.Int):
        return any(isinstance(orig, ty) for ty in [retic_ast.Int, retic_ast.Bool, retic_ast.SingletonInt])
    elif isinstance(into, retic_ast.Function) and isinstance(orig, retic_ast.Function):
        return assignable(into.to, orig.to) and\
            param_assignable(into.froms, orig.froms)
    elif isinstance(into, retic_ast.HTuple) and isinstance(orig, retic_ast.Tuple):
        return all(consistent(into.elts, oelt) for oelt in orig.elts)
    elif isinstance(into, retic_ast.HTuple) and isinstance(orig, retic_ast.List):
        return consistent(into.elts, orig.elts)
    #if a single type, then is it assinable to anything in the union
    #else, check if *any* of the types are assignable to anything in the union
    elif isinstance(into, retic_ast.Union):
        if not isinstance(orig, retic_ast.Union):
            return any(assignable(t, orig) for t in into.alternatives)
        else:
            for t1 in into.alternatives:
                return any(assignable(t1, t2) for t2 in orig.alternatives)
    elif isinstance(into, retic_ast.Instance) and isinstance(orig, retic_ast.Instance):
        return orig.instanceof.subtype_of(into.instanceof)
    elif isinstance(into, retic_ast.Structural) and isinstance(orig, retic_ast.Structural):
        return all(k in orig.members and consistent(into.members[k], orig.members[k]) for k in into.members)
    elif isinstance(into, retic_ast.Structural) and isinstance(orig, retic_ast.Instance):
        try:
            return all(consistent(into.members[k], orig[k]) for k in into.members)
        except KeyError:
            return False
    elif isinstance(into, retic_ast.Structural) and isinstance(orig, retic_ast.Class):
        try:
            return all(consistent(into.members[k], orig[k]) for k in into.members)
        except KeyError:
            return False
    else:
        return False

# Function contravariance happens here
def param_assignable(into: retic_ast.ArgTypes, orig: retic_ast.ArgTypes)->bool:
    if param_consistent(into, orig):
        return True
    elif isinstance(into, retic_ast.PosAT):
        if isinstance(orig, retic_ast.PosAT):
            return len(orig.types) == len(into.types) and \
                all(assignable(t1a, t2a) for t1a, t2a in zip(orig.types, into.types))
        elif isinstance(orig, retic_ast.SpecAT):
            try:
                ba = orig.spec.bind(*into.types)
            except TypeError:
                return False
            for key in ba.arguments:
                _, pty = argspec.paramty(key, orig.spec) 
                if isinstance(ba.arguments[key], tuple):
                    if any(not assignable(pty, t1) for t1 in ba.arguments[key]):
                        return False
                elif isinstance(ba.arguments[key], dict):
                    raise Exception()
                elif isinstance(ba.arguments[key], retic_ast.Type):
                    if not assignable(pty, ba.arguments[key]):
                        return False
            return True
        # elif isinstance(orig, retic_ast.NamedAT):
        #     return len(orig.bindings) == len(into.types) and \
        #         all(assignable(t1a, t2a) for (_, t1a), t2a in zip(orig.bindings, into.types))
        # elif isinstance(orig, retic_ast.ApproxNamedAT):
        #     return all(assignable(t1a, t2a) for (_, t1a), t2a in zip(orig.bindings, into.types))
        # else: raise exc.UnimplementedException(orig)
    elif isinstance(into, retic_ast.SpecAT):
        if isinstance(orig, retic_ast.SpecAT):
            param_pairs = argspec.padjoin(into.spec, orig.spec)
            
            for ti, to in param_pairs:
                if ti:
                    if to:
                        if not (ti.name == to.name and assignable(to, ti)):
                            return False
                    else:
                        return False
                else:
                    return to.default is not inspect.Parameter.empty
            return True
        else: return False
    # elif isinstance(into, retic_ast.NamedAT):
    #     if isinstance(orig, retic_ast.NamedAT):
    #         return len(orig.bindings) == len(into.bindings) and \
    #             all(k1 == k2 and assignable(t1a, t2a) for (k1, t1a), (k2, t2a) in zip(orig.bindings, into.bindings))
    #     elif isinstance(orig, retic_ast.ApproxNamedAT):
    #         return all(k1 == k2 and assignable(t1a, t2a) for (k1, t1a), (k2, t2a) in zip(orig.bindings, into.bindings))
    #     else: return False
    # elif isinstance(into, retic_ast.ApproxNamedAT):
    #     if isinstance(orig, retic_ast.ApproxNamedAT):
    #         return all(k1 == k2 and assignable(t1a, t2a) for (k1, t1a), (k2, t2a) in zip(orig.bindings, into.bindings))
    #     else: return False
    else:
        raise exc.UnimplementedException(into)
    
            
class BadTypeOp(Exception): pass

# Member assignabilty sees if the members of the RHS can be written into the LHS.
def member_assignable(l: retic_ast.Type, r: retic_ast.Type):
    try:
        itr = iterable_type(r)
        return assignable(l, itr)
    except BadTypeOp:
        return False

# Instance assignability holds if an instance of the type on the RHS can be written into the LHS.
def instance_assignable(l: retic_ast.Type, r: retic_ast.Type):
    try:
        instr = instance_type(r)
        return assignable(l, instr)
    except BadTypeOp:
        return False

# Iterable type gets the type of the resulting values when the type is iterated over,
# or False if the type cannot be iterated over
def iterable_type(ty: retic_ast.Type):
    if isinstance(ty, retic_ast.Bot):
        return retic_ast.Bot()
    elif isinstance(ty, retic_ast.Dyn):
        return retic_ast.Dyn()
    elif isinstance(ty, retic_ast.Str):
        return retic_ast.Str()
    elif isinstance(ty, retic_ast.List):
        return ty.elts
    elif isinstance(ty, retic_ast.Set):
        return ty.elts
    elif isinstance(ty, retic_ast.Dict):
        return ty.keys
    elif isinstance(ty, retic_ast.HTuple):
        return ty.elts
    elif isinstance(ty, retic_ast.Tuple):
        return join(*ty.elts)
    else: 
        raise BadTypeOp(ty)

# Instance type gets the type of an instantiation of the type
# or False if the type cannot be instantiated
def instance_type(ty: retic_ast.Type):
    if isinstance(ty, retic_ast.Bot):
        return retic_ast.Bot()
    elif isinstance(ty, retic_ast.Dyn):
        return retic_ast.Dyn()
    elif isinstance(ty, retic_ast.Class):
        ret = retic_ast.Instance(ty)
        return ret
    else: 
        raise BadTypeOp(ty)


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
    if isinstance(ty, retic_ast.SingletonInt):
        ty = retic_ast.Int()
    for typ in tys[1:]:
        if isinstance(typ, retic_ast.Bot):
            continue
        elif ty == typ:
            continue
        elif isinstance(ty, retic_ast.Bot):
            ty = typ
        elif isinstance(typ, retic_ast.SingletonInt):
            if isinstance(ty, retic_ast.Int):
                continue
            else: return retic_ast.Dyn() 
        elif isinstance(typ, retic_ast.Primitive) and isinstance(ty, retic_ast.Primitive) and \
           ty.__class__ is typ.__class__:
            continue
        elif isinstance(typ, retic_ast.Function) and isinstance(ty, retic_ast.Function):
            ty = retic_ast.Function(param_join(ty.froms, typ.froms),
                                    join(ty.to, typ.to))
        elif isinstance(typ, retic_ast.List) and isinstance(ty, retic_ast.List):
            ty = retic_ast.List(join(typ.elts, ty.elts))
        elif isinstance(typ, retic_ast.Set) and isinstance(ty, retic_ast.Set):
            ty = retic_ast.Set(join(typ.elts, ty.elts))
        elif isinstance(typ, retic_ast.Dict) and isinstance(ty, retic_ast.Dict):
            ty = retic_ast.Dict(join(typ.keys, ty.keys), join(typ.values, ty.values))
        elif isinstance(typ, retic_ast.HTuple) and isinstance(ty, retic_ast.HTuple):
            ty = retic_ast.HTuple(join(typ.elts, ty.elts))
        elif isinstance(typ, retic_ast.Tuple) and isinstance(ty, retic_ast.Tuple) and len(typ.elts) == len(ty.elts):
            ty = retic_ast.Tuple(*[join(p, y) for p, y in zip(typ.elts, ty.elts)])
        elif isinstance(typ, retic_ast.Tuple) and isinstance(ty, retic_ast.Tuple) and len(typ.elts) != len(ty.elts):
            ty = retic_ast.HTuple(join(*(typ.elts + ty.elts)))
        elif isinstance(typ, retic_ast.Structural) and isinstance(ty, retic_ast.Structural):
            ty = retic_ast.Structural({k: join(ty.members[k], typ.members[k]) for k in ty.members if k in typ.members})
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
    elif isinstance(p1, retic_ast.SpecAT) and isinstance(p2, retic_ast.SpecAT):
        param_pairs = argspec.padjoin(p1.spec, p2.spec)
        ret = []
        for t1, t2 in param_pairs:
            if not t1 or not t2:
                return retic_ast.ArbAT()
            if t1.name == t2.name and t1.kind == t2.kind and ((t1.default and t2.default) or t1.default == t2.default):
                ret += inspect.Parameter(t1.name, t1.kind, default=t1.default, annotation=join(t1.annotation, t2.annotation))
            else: return retic_ast.ArbAT()
        return retic_ast.SpecAT(inspect.Signature(ret))
    # elif isinstance(p1, retic_ast.NamedAT) and isinstance(p2, retic_ast.NamedAT):
    #     if len(p1.bindings) == len(p2.bindings) and \
    #        all([k1 == k2 for (k1, _), (k2, _) in zip(p1.bindings, p2.bindings)]):
    #         return retic_ast.NamedAT([(k, join(t1, t2)) for (k, t1), (_, t2) in zip(p1.bindings, p2.bindings)])
    #     else:
    #         return retic_ast.ArbAT()
    # elif isinstance(p1, retic_ast.ApproxNamedAT) and isinstance(p2, retic_ast.ApproxNamedAT):
    #     if all([k1 == k2 for (k1, _), (k2, _) in zip(p1.bindings, p2.bindings)]):
    #         return retic_ast.NamedAT([(k, join(t1, t2)) for (k, t1), (_, t2) in zip(p1.bindings, p2.bindings)])
    #     else:
    #         return retic_ast.ArbAT()
    else:
        return retic_ast.ArbAT()
            

def getop(op:ast.operator)->typing.Callable[[int, int], int]:
    if isinstance(op, ast.Add):
        return lambda x, y: x + y
    elif isinstance(op, ast.Sub):
        return lambda x, y: x - y
    elif isinstance(op, ast.Pow):
        return lambda x, y: x ** y
    elif isinstance(op, ast.FloorDiv):
        return lambda x, y: x // y
    elif isinstance(op, ast.LShift):
        return lambda x, y: x << y
    elif isinstance(op, ast.RShift):
        return lambda x, y: x >> y
    elif isinstance(op, ast.BitOr):
        return lambda x, y: x | y
    elif isinstance(op, ast.BitAnd):
        return lambda x, y: x & y
    elif isinstance(op, ast.BitXor):
        return lambda x, y: x ^ y
    elif isinstance(op, ast.Mod):
        return lambda x, y: x % y
    elif isinstance(op, ast.Mult):
        return lambda x, y: x * y
    else: raise exc.InternalReticulatedError(op)

def getopmeth(op:ast.operator):
    if isinstance(op, ast.Add):
        return '__add__', '__radd__'
    elif isinstance(op, ast.Sub):
        return '__sub__', '__rsub__'
    elif isinstance(op, ast.Pow):
        return '__pow__', '__rpow__'
    elif isinstance(op, ast.Div):
        return '__truediv__', '__rtruediv__'
    elif isinstance(op, ast.FloorDiv):
        return '__floordiv__', '__rfloordiv__'
    elif isinstance(op, ast.LShift):
        return '__lshift__', '__rlshift__'
    elif isinstance(op, ast.RShift):
        return '__rshift__', '__rrshift__'
    elif isinstance(op, ast.BitOr):
        return '__or__', '__ror__'
    elif isinstance(op, ast.BitAnd):
        return '__and__', '__rand__'
    elif isinstance(op, ast.BitXor):
        return '__xor__', '__rxor__'
    elif isinstance(op, ast.Mod):
        return '__mod__', '__rmod__'
    elif isinstance(op, ast.Mult):
        return '__mul__', '__mul__'
    else: raise exc.InternalReticulatedError(op)
            
def apply_binop(ln, rn, op: ast.operator, l:retic_ast.Type, r:retic_ast.Type):
    def apply_binop_method(l, r):
        lmeth, rmeth = getopmeth(op)
        try: 
            lfunc = l[lmeth]
            ty, tyerr = apply(ln, lfunc, [rn], [], None, None)
            if tyerr:
                return False
            else: return ty
        except KeyError:
            try:
                rfunc = r[rmeth]
                ty, tyerr = apply(rn, rfunc, [ln], [], None, None)
                if tyerr:
                    return False
                else: return ty
            except KeyError:
                return False


    if isinstance(l, retic_ast.Dyn):
        return retic_ast.Dyn()
    elif (not isinstance(op, ast.Mod) or not isinstance(l, retic_ast.Str))\
         and isinstance(r, retic_ast.Dyn): # If LHS is a string and op is %, then we def have a string
        return retic_ast.Dyn()
    elif isinstance(op, ast.Add):
        if isinstance(l, retic_ast.SingletonInt) and isinstance(r, retic_ast.SingletonInt):
            return retic_ast.SingletonInt(l.n + r.n)
        elif assignable(retic_ast.Int(), l) and assignable(retic_ast.Int(), r):
            return retic_ast.Int()
        elif assignable(retic_ast.Float(), l) and assignable(retic_ast.Float(), r):
            return retic_ast.Float()
        elif assignable(retic_ast.Str(), l) and assignable(retic_ast.Str(), r):
            return retic_ast.Str()
        elif assignable(retic_ast.List(retic_ast.Dyn()), l) and assignable(retic_ast.List(retic_ast.Dyn()), r):
            return join(l, r)
        elif assignable(retic_ast.HTuple(retic_ast.Dyn()), l) and assignable(retic_ast.HTuple(retic_ast.Dyn()), r):
            return join(l, r)
        elif isinstance(l, retic_ast.Tuple) and isinstance(r, retic_ast.Tuple):
            return retic_ast.Tuple(*(l.elts + r.elts))
        else: 
            return apply_binop_method(l, r)
    elif isinstance(op, ast.Sub) or isinstance(op, ast.Pow): # These ones can take floats
        if isinstance(l, retic_ast.SingletonInt) and isinstance(r, retic_ast.SingletonInt):
            return retic_ast.SingletonInt(getop(op)(l.n, r.n))
        elif assignable(retic_ast.Int(), l) and assignable(retic_ast.Int(), r):
            return retic_ast.Int()
        elif assignable(retic_ast.Float(), l) and assignable(retic_ast.Float(), r):
            return retic_ast.Float()
        else: 
            return apply_binop_method(l, r)
    elif isinstance(op, ast.Div):
        if assignable(retic_ast.Float(), l) and assignable(retic_ast.Float(), r):
            return retic_ast.Float()
        else: 
            return apply_binop_method(l, r)
    elif isinstance(op, ast.FloorDiv): # Takes floats, but always return int
        if isinstance(l, retic_ast.SingletonInt) and isinstance(r, retic_ast.SingletonInt):
            return retic_ast.SingletonInt(getop(op)(l.n, r.n))
        elif assignable(retic_ast.Float(), l) and assignable(retic_ast.Float(), r):
            return retic_ast.Int()
        else: 
            return apply_binop_method(l, r)
    elif isinstance(op, ast.LShift) or isinstance(op, ast.RShift) or \
         isinstance(op, ast.BitOr) or isinstance(op, ast.BitXor) or isinstance(op, ast.BitAnd): # These ones cant
        if isinstance(l, retic_ast.SingletonInt) and isinstance(r, retic_ast.SingletonInt):
            return retic_ast.SingletonInt(getop(op)(l.n, r.n))
        elif assignable(retic_ast.Int(), l) and assignable(retic_ast.Int(), r):
            return retic_ast.Int()
        else: 
            return apply_binop_method(l, r)
    elif isinstance(op, ast.Mod): # Can take floats
        if isinstance(l, retic_ast.SingletonInt) and isinstance(r, retic_ast.SingletonInt):
            return retic_ast.SingletonInt(getop(op)(l.n, r.n))
        elif assignable(retic_ast.Int(), l) and assignable(retic_ast.Int(), r):
            return retic_ast.Int()
        elif assignable(retic_ast.Float(), l) and assignable(retic_ast.Float(), r):
            return retic_ast.Float()
        elif assignable(retic_ast.Str(), l):
            return retic_ast.Str()
        else: 
            return apply_binop_method(l, r)
    elif isinstance(op, ast.Mult): # Can take floats
        if isinstance(l, retic_ast.SingletonInt) and isinstance(r, retic_ast.SingletonInt):
            return retic_ast.SingletonInt(getop(op)(l.n, r.n))
        elif assignable(retic_ast.Int(), l) and assignable(retic_ast.Int(), r):
            return retic_ast.Int()
        elif assignable(retic_ast.Float(), l) and assignable(retic_ast.Float(), r):
            return retic_ast.Float()
        if assignable(retic_ast.Str(), l) and assignable(retic_ast.Int(), r):
            return retic_ast.Str()
        if assignable(retic_ast.Int(), l) and assignable(retic_ast.Str(), r):
            return retic_ast.Str()
        if isinstance(l, retic_ast.List) and assignable(retic_ast.Int(), r):
            return l
        if assignable(retic_ast.Int(), l) and isinstance(r, retic_ast.List):
            return r
        else: 
            return apply_binop_method(l, r)
    else:
        raise InternalReticulatedError(op)

def apply_unop(op: ast.unaryop, o:retic_ast.Type):
    if isinstance(o, retic_ast.Dyn):
        return retic_ast.Dyn()
    elif isinstance(op, ast.Not):
        return retic_ast.Bool()
    elif isinstance(op, ast.Invert):
        if isinstance(o, retic_ast.SingletonInt):
            return retic_ast.SingletonInt(~ o.n)
        elif assignable(retic_ast.Int(), o): 
            return retic_ast.Int()
        else:
            return False
    elif isinstance(op, ast.UAdd) or isinstance(op, ast.USub):
        if isinstance(o, retic_ast.SingletonInt):
            return retic_ast.SingletonInt(o.n if isinstance(op, ast.UAdd) else -o.n)
        elif assignable(retic_ast.Int(), o): #yes float
            return retic_ast.Int()
        elif assignable(retic_ast.Float(), o): 
            return retic_ast.Float()
        else:
            return False

def setter_curry(n:ast.expr, methodty: retic_ast.Type, setty: retic_ast.Type):
    def curry_types(into, expect):
        if not assignable(into, setty):
            raise exc.StaticTypeError(n, 'Cannot set with a target of type {}; a value of type {} was expected'.format(val.retic_type, into))
        else: 
            return expect

    if isinstance(methodty, retic_ast.Dyn):
        return retic_ast.Dyn()
    elif isinstance(methodty, retic_ast.Function):
        if isinstance(methodty.froms, retic_ast.ArbAT):
            return retic_ast.Dyn()
        elif isinstance(methodty.froms, retic_ast.PosAT):
            if len(methodty.froms.types) != 2:
                raise exc.InternalReticulatedError()
            else: return curry_types(methodty.froms.types[0], methodty.froms.types[1])
        elif isinstance(methodty.froms, retic_ast.PosAT):
            if len(methodty.froms.types) != 2:
                raise exc.InternalReticulatedError()
            else: return curry_types(methodty.froms.types[0], methodty.froms.types[1])
        elif isinstance(methodty.froms, retic_ast.SpecAT):
            if len(methodty.froms.spec.parameters) != 2:
                raise exc.InternalReticulatedError()
            else: return curry_types(methodty.froms.spec.parameters[list(methodty.froms.spec.parameters)[0]].annotation,
                                     methodty.froms.spec.parameters[list(methodty.froms.spec.parameters)[1]].annotation)
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
