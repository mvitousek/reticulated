from .. import visitors, retic_ast, typing, exc, flags
from .constraints import *
from . import ctypes, cgen_helpers, cscopes
from functools import reduce
import ast

def U(args):
    return reduce(set.union, args, set())

# Major Todo Items:
# - Return checking pass for constraints on return types
# - Decomposing assignment, including making sure that variables are preserved
# - Making sure that function arguments have variables
# - Primitive stuff, e.g. binops
# - Comprehension stuff
# - Functions calls 
# - Attribute access
# - Slicing

class ConstraintGenerator(visitors.SetGatheringVisitor):

    def visitlist(self, n, *args):
        st = set()
        for s in n:
            st |= self.dispatch(s, *args)
        return st
        
    def visitNoneType(self, n, *args):
        return set()

    def visitModule(self, n):
        # Need to have gathered an initial environment of type variables
        # Also need to detect globally visible type variables -- probably the same pass
        env = n.retic_cenv
        ctbl = n.retic_cctbl
        return self.dispatch(n.body, env, ctbl)

    def visitClassDef(self, n, env, ctbl, *args):
        st = U([self.dispatch(dec, env, ctbl, *args) for dec in n.decorator_list])
        st |= U([self.dispatch(base, env, ctbl, *args) for base in n.bases])
        inherits = [base.retic_ctype for base in n.bases]
        st |= {InheritsC(inherits, n.name)}
        st |= U([self.dispatch(kwd.value, env, ctbl, *args) for kwd in n.keywords])
        return st | self.dispatch(n.body, n.retic_cenv, ctbl, *args)


    def visitFunctionDef(self, n, env, ctbl, *args):
        fun_env = n.retic_cenv

        st = self.dispatch(n.args, env, ctbl, *args)
        st |= U([self.dispatch(dec, env, ctbl, *args) for dec in n.decorator_list])
        if n.retic_ismethod:
            st |= {STC(n.retic_ismethod, n.args.args[0].retic_ctype)}
        
        return st | self.dispatch(n.body, fun_env, ctbl, *args)
        

    def visitarguments(self, n, *args):
        st = U([self.dispatch(default, *args) for default in n.defaults])
        st |= U([self.dispatch(arg, *args) for arg in n.args])
        st |= U([self.dispatch(arg, *args) for arg in n.kwonlyargs])
        st |= U([self.dispatch(default, *args) for default in n.kw_defaults])
        st |= self.dispatch(n.kwarg, *args)
        st |= self.dispatch(n.vararg, *args)

        # Check to make sure that any default arguments are well typed:
        if n.defaults:
            matches = n.args[-len(n.defaults):]
            st |= {STC(dflt.retic_ctype, arg.retic_ctype) for arg, dflt in zip(matches, n.defaults)}

        if n.kw_defaults:
            matches = n.kwonlyargs[-len(n.kw_defaults):]
            st |= {STC(dflt.retic_ctype, arg.retic_ctype) for arg, dflt in zip(matches, n.kw_defaults)}

        return st
                    

    def visitarg(self, n, *args):
        return self.dispatch(n.annotation, *args)

    def visitReturn(self, n, *args):
        # Handle return type checking in a separate pass
        return self.dispatch(n.value, *args)

    # Assignment stuff
    def visitAssign(self, n, *args):
        st = self.dispatch(n.value, *args)
        for target in n.targets:
            st |= self.dispatch(target, *args)
            assigns, stp = cscopes.decomp_assign(target, n.value.retic_ctype)
            st |= stp
            for subtarg in assigns:
                st |= {STC(assigns[subtarg], subtarg.retic_ctype)}
        return st

    def visitAugAssign(self, n, *args):
        st = self.dispatch(n.value, *args)
        st |= self.dispatch(n.target, *args)
        Lots(Todo)

    def visitFor(self, n, *args):
        st = self.dispatch(n.target, *args)
        st |= self.dispatch(n.iter, *args)
        st |= {EltSTC(n.iter.retic_ctype, n.target.retic_ctype)}
        st |= self.dispatch(n.body, *args)
        st |= self.dispatch(n.orelse, *args)
        return st

    def visitWith(self, n, *args): 
        st = self.dispatch(n.body, *args)
        if flags.PY_VERSION == 3 and flags.PY3_VERSION >= 3:
            return st | U([self.dispatch(item, *args) for item in n.items])
        else:
            st |= self.dispatch(n.context_expr, *args)
            if n.optional_vars:
                st |= self.dispatch(n.optional_vars, *args)
                st |= {STC(n.optional_vars.retic_ctype, n.context_expr.retic_ctype)}
            return st

    def visitwithitem(self, n, *args):
        st = self.dispatch(n.context_expr, *args)
        if n.optional_vars:
            st |= self.dispatch(n.optional_vars, *args)
            st |= {STC(n.optional_vars.retic_ctype, n.context_expr.retic_ctype)}
        return st


    def visitExceptHandler(self, n, env, *args):
        st = self.dispatch(n.type, env, *args)
        st |= self.dispatch(n.body, env, *args)
        
        if n.name and n.name in env:
            ty = env[n.name]
        else:
            ty = ctypes.CDyn()
        n.retic_ctype = ty
        return st | {InstanceSTC(n.type.retic_ctype, ty)}

### EXPRESSIONS ###
    # Op stuff
    def visitBoolOp(self, n, *args):
        ty = ctypes.CVar(name='boolop')
        n.retic_ctype = ty
        st = set()
        for val in n.values:
            st |= self.dispatch(val, *args) | {STC(val.retic_ctype, ty)}
        return st

    def visitBinOp(self, n, *args):
        st = self.dispatch(n.left, *args)
        st |= self.dispatch(n.right, *args)
        ty = ctypes.CVar(name='binop')
        n.retic_ctype = ty
        ret = st | {BinopSTC(n.op, n.left.retic_ctype, n.right.retic_ctype, ty)}
        return ret

    def visitUnaryOp(self, n, *args):
        st = self.dispatch(n.operand, *args)
        ty = ctypes.CVar(name='unop')
        n.retic_ctype = ty
        return st | {UnopSTC(n.op, n.operand.retic_ctype, ty)}

    def visitCompare(self, n, *args):
        st = self.dispatch(n.left, *args)
        st |= self.dispatch(n.comparators, *args)
        # Some rather complicated logic needed here to reject objects that definitely don't have __lt__ etc
        n.retic_ctype = ctypes.CBool()
        return st
        
    # Collections stuff    
    def visitList(self, n, *args):
        st = set()
        ty = ctypes.CVar(name='list')
        for val in n.elts:
            st |= self.dispatch(val, *args) | {STC(val.retic_ctype, ty)}
        n.retic_ctype = ctypes.CList(ty)
        return st

    def visitTuple(self, n, *args):
        tys = []
        st = set()
        for val in n.elts:
            st |= self.dispatch(val, *args)
            ty = ctypes.CVar(name='tupleelt')
            st |= {STC(val.retic_ctype, ty)}
            tys.append(ty)
        n.retic_ctype = ctypes.CTuple(*tys)
        return st

    def visitDict(self, n, *args):
        kty = ctypes.CVar(name='dictkey')
        vty = ctypes.CVar(name='dictval')
        st = set()
        for key in n.keys:
            st |= self.dispatch(key, *args) | {STC(key.retic_ctype, kty)}
        for val in n.values:
            st |= self.dispatch(val, *args) | {STC(val.retic_ctype, vty)}
        n.retic_ctype = ctypes.CDict(kty, vty)
        return st

    def visitSet(self, n, *args):
        st = set()
        ty = ctypes.CVar(name='set')
        for val in n.elts:
            st |= self.dispatch(val, *args) | {STC(val.retic_ctype, ty)}
        n.retic_ctype = ctypes.CSet(ty)
        return st

    def visitListComp(self, n, env, *args):
        # Don't dispatch on the generators -- that will be done by getComprehensionScope
        comp_env, st = cscopes.getComprehensionScope(n.generators, env, self, *args)
        st |= self.dispatch(n.elt, comp_env, *args)
        ty = ctypes.CVar(name='listcomp')
        st |= {STC(n.elt.retic_ctype, ty)}
        n.retic_ctype = ctypes.CList(ty)
        return st

    def visitSetComp(self, n, env, *args):
        comp_env, st = cscopes.getComprehensionScope(n.generators, env, self, *args)
        st |= self.dispatch(n.elt, comp_env, *args)
        ty = ctypes.CVar(name='setcomp')
        st |= {STC(n.elt.retic_ctype, ty)}
        n.retic_ctype = ctypes.CSet(ty)
        return st

    def visitDictComp(self, n, env, *args):
        comp_env, st = cscopes.getComprehensionScope(n.generators, env, self, *args)
        st |= self.dispatch(n.key, comp_env, *args)
        st |= self.dispatch(n.value, comp_env, *args)
        key = ctypes.CVar(name='dictcompkey')
        val = ctypes.CVar(name='dictcompval')
        st |= {STC(n.key.retic_ctype, key), STC(n.value.retic_ctype, val)}
        n.retic_ctype = ctypes.CDict(key, val)
        return st

    def visitGeneratorExp(self, n, env, *args):
        comp_env, st = cscopes.getComprehensionScope(n.generators, env, self, *args)
        st |= self.dispatch(n.elt, comp_env, *args)
        n.retic_ctype = ctypes.CDyn()
        return st | {EqC(n.elt.retic_ctype, ctypes.CDyn())}
        

    def visitcomprehension(self, n, *args):
        raise exc.InternalReticulatedError('Comprehensions should not be visited directly')

    # Control flow stuff
    def visitYield(self, n, *args):
        n.retic_ctype = ctypes.CDyn()
        return self.dispatch(n.value, *args)

    def visitYieldFrom(self, n, *args):
        n.retic_ctype = ctypes.CDyn()
        return self.dispatch(n.value, *args)

    def visitIfExp(self, n, *args):
        ty = ctypes.CVar(name='ifexp')
        st = self.dispatch(n.test, *args)
        st |= self.dispatch(n.body, *args)
        st |= self.dispatch(n.orelse, *args)
        n.retic_ctype = ty
        return st | {STC(n.body.retic_ctype, ty), STC(n.orelse.retic_ctype, ty)}

    # Function stuff
    def visitCall(self, n, env, ctbl, *args):
        st = self.dispatch(n.func, env, ctbl, *args)
        st |= self.dispatch(n.args, env, ctbl, *args)
        st |= U([self.dispatch(k.value, env, ctbl, *args) for k in n.keywords])
        st |= self.dispatch(n.starargs, env, ctbl, *args) if getattr(n, 'starargs', None) else set()
        st |= self.dispatch(n.kwargs, env, ctbl, *args) if getattr(n, 'kwargs', None) else set()

        if flags.PY3_VERSION <= 4:
            args, starargs, keywords, kwargs = n.args, n.starargs, n.keywords, n.kwargs
        else:
            args = [a for a in n.args if not isinstance(a, ast.Starred)]
            starargs = [a.value for a in n.args if isinstance(a, ast.Starred)]
            keywords = [k for k in n.keywords if k.arg is not None]
            kwargs = [k.value for k in n.keywords if k.arg is None]
            if len(starargs) > 1 or len(kwargs) > 1:
                raise Exception()
            else:
                starargs = starargs[0] if len(starargs) else None
                kwargs = kwargs[0] if len(kwargs) else None
            
        ty, stp = cgen_helpers.apply(n.func, n.func.retic_ctype, args, keywords,
                                     starargs, kwargs, ctbl)
        
        n.retic_ctype = ty
        return st | stp


    def visitLambda(self, n, env, *args):
        lam_env = cscopes.getLambdaScope(n, env)
        st = self.dispatch(n.args, env, *args)
        st |= self.dispatch(n.body, lam_env, *args)

        argtys = []
        for arg in n.args.args:
            argty = ctypes.CVar(name=arg.arg)
            argtys.append(argty)

        retty = ctypes.CVar(name='lambdareturn')

        n.retic_ctype = ctypes.CFunction(ctypes.PosCAT(argtys), retty)
        return st | {STC(n.body.retic_ctype, retty)}

    # Variable stuff
    def visitAttribute(self, n, env, ctbl, *args):
        st = self.dispatch(n.value, env, ctbl, *args)
        var = ctypes.CVar('attr')
        new_type = ctypes.ctype_match(var, retic_ast.Structural({n.attr: retic_ast.Dyn()}), ctbl)
        st |= {CheckC(n.value.retic_ctype, retic_ast.Structural({n.attr: retic_ast.Dyn()}), new_type), EqC(var, n.value.retic_ctype)}

        n.retic_ctype = new_type.lookup(n.attr, ctbl)
        return st

    def visitSubscript(self, n, *args):
        st = self.dispatch(n.value, *args)
        st |= self.dispatch(n.slice, n.value.retic_ctype, n, *args)
        n.retic_ctype = n.slice.retic_ctype
        return st

    def visitIndex(self, n, orig_type, orig_node, env, ctbl, *args):
        st = self.dispatch(n.value, env, ctbl, *args)
        var = ctypes.CVar('index')
        new_type = ctypes.ctype_match(var, retic_ast.Subscriptable(), ctbl)
        st |= {CheckC(orig_type, retic_ast.Subscriptable(), new_type), EqC(var, orig_type)}
        
        if isinstance(new_type, ctypes.CSubscriptable):
            st |= {STC(n.value.retic_ctype, new_type.keys)}
            n.retic_ctype = new_type.elts
        elif isinstance(new_type, ctypes.CStr):
            n.retic_ctype = ctypes.CStr()
        elif isinstance(new_type, ctypes.CList) or isinstance(new_type, ctypes.CHTuple):
            n.retic_ctype = new_type.elts
        elif isinstance(new_type, ctypes.CTuple):
            if isinstance(n.value.retic_ctype, ctypes.CSingletonInt):
                n.retic_ctype = new_type.elts[n.value.retic_ctype.n]
            else:
                n.retic_ctype = ctypes.CVar(name='tuplejoin')
                st |= {STC(elt, n.retic_ctype) for elt in new_type.elts}
        elif isinstance(new_type, ctypes.CDict):
            n.retic_ctype = new_type.values
        elif isinstance(new_type, ctypes.CInstance):
            if isinstance(orig_node.ctx, ast.Store):
                ixt = new_type['__setitem__']
                n.retic_ctype, stp = cgen_helpers.setter_curry(orig_node, ixt, n.value.retic_ctype)
                st |= stp
            elif isinstance(orig_node.ctx, ast.Load):
                ixt = new_type['__getitem__']
                n.retic_ctype, stp = cgen_helpers.apply(orig_node, ixt, [n.value], [], None, None, ctbl)
                st |= stp
            else:
                raise exc.InternalReticulatedError()
        else:
            raise exc.InternalReticulatedError(new_type)
        return st


    def visitSlice(self, n, orig_type, orig_node, env, ctbl, *args):
        st = self.dispatch(n.lower, env, ctbl, *args)
        st |= self.dispatch(n.upper, env, ctbl, *args)
        st |= self.dispatch(n.step, env, ctbl, *args)

        var = ctypes.CVar('slice')
        new_type = ctypes.ctype_match(var, retic_ast.Subscriptable(), ctbl)
        st |= {CheckC(orig_type, retic_ast.Subscriptable(), new_type), EqC(var, orig_type)}

        if isinstance(new_type, ctypes.CSubscriptable):
            if n.lower:
                st |= {STC(n.lower.retic_ctype, new_type.keys)}
            if n.upper:
                st |= {STC(n.upper.retic_ctype, new_type.keys)}
            if n.step:
                st |= {STC(n.step.retic_ctype, new_type.keys)}
            n.retic_ctype = new_type
        elif isinstance(orig_type, ctypes.CStr):
            n.retic_ctype = ctypes.CStr()
        elif isinstance(orig_type, ctypes.CList) or isinstance(orig_type, ctypes.CHTuple):
            n.retic_ctype = new_type
        elif isinstance(orig_type, ctypes.CTuple):
            n.retic_ctype = ctypes.CHTuple(ctypes.CVar(name='tuplejoin'))
            stp = {STC(elt, n.retic_ctype.elts) for elt in orig_type.elts}
                
            # If we have all singletons, we can refine this to an actual tuple type
            if (n.lower and isinstance(n.lower.retic_ctype, ctypes.CSingletonInt)) or not n.lower:
                if not n.lower:
                    low = 0
                else: low = n.lower.n
                
                if (n.upper and isinstance(n.upper.retic_ctype, ctypes.CSingletonInt)) or not n.upper:
                    if not n.upper:
                        up = len(orig_type.elts)
                    else: up = n.upper.n
                    
                    if (n.step and isinstance(n.step.retic_ctype, ctypes.CSingletonInt)) or not n.step:
                        if not n.step:
                            step = 1
                        else: step = n.step.n
                        n.retic_ctype = ctypes.CTuple(*orig_type.elts[low:up:step])
                        return st
            st |= stp
        elif isinstance(orig_type, ctypes.CInstance):
            # See typechecker for some discussion of this
            # weirdness. For now, I'm just using the original value's
            # type.
            if isinstance(orig_node.ctx, ast.Store):
                ixt = orig_type['__setitem__']
                n.retic_ctype, stp = cgen_helpers.setter_curry(orig_node, ixt, n.value.retic_ctype)
                st |= stp
            elif isinstance(orig_node.ctx, ast.Load):
                ixt = orig_type['__getitem__']
                n.retic_ctype, stp = cgen_helpers.apply(orig_node, ixt, [n.value], [], None, None)
                st |= stp
            else: raise exc.InternalReticulatedError()
        else:
            raise exc.InternalReticulatedError()
        return st

    def visitExtSlice(self, n, orig_type, orig_node, *args):
        # I have no idea what to do with ExtSlices and I can't find an
        # example where they're used, so...
        n.retic_ctype = ctypes.CDyn()
        return self.dispatch(n.dims, *args)

    def visitStarred(self, n, *args):
        # Starrd exps can only be assignment targets. The starred
        # thing had better be an iterable thing like a list or tuple,
        # I think
        st = self.dispatch(n.value, *args)
        n.retic_ctype = n.value.retic_ctype
        return st

    def visitNameConstant(self, n, *args):
        if n.value is True or n.value is False:
            n.retic_ctype = ctypes.CBool()
        elif n.value is None:
            n.retic_ctype = ctypes.CVoid()
        else: 
            raise exc.InternalReticulatedError('NameConstant', n.value)
        return set()

    def visitName(self, n, env, *args):
        n.retic_ctype = env[n.id]
        return set()

    def visitNum(self, n, *args):
        if isinstance(n.n, int):
            n.retic_ctype = ctypes.CSingletonInt(n.n)
        elif isinstance(n.n, float):
            n.retic_ctype = ctypes.CFloat()
        else:
            n.retic_ctype = ctypes.CDyn()
        return set()

    def visitStr(self, n, *args):
        n.retic_ctype = ctypes.CStr()
        return set()

    def visitBytes(self, n, *args):
        n.retic_ctype = ctypes.CDyn()
        return set()

    def visitEllipsis(self, n, *args):
        n.retic_ctype = ctypes.CDyn()
        return set()

    def visitCheck(self, n, env, ctbl, *args):
        st = self.dispatch(n.value, env, ctbl, *args)
        var = ctypes.CVar('check')
        ty = ctypes.ctype_match(var, n.type, ctbl)
        n.retic_ctype = ty
        return st | {CheckC(n.value.retic_ctype, n.type, ty), EqC(var, n.value.retic_ctype)}

    def visitUseCheck(self, n, env, ctbl, *args):
        st = self.dispatch(n.value, env, ctbl, *args)
        var = ctypes.CVar('check')
        ty = ctypes.ctype_match(var, n.type, ctbl)
        n.retic_ctype = ty
        return st | {CheckC(n.value.retic_ctype, n.type, ty), EqC(var, n.value.retic_ctype)}

    def visitProtCheck(self, n, env, ctbl, *args):
        st = self.dispatch(n.value, env, ctbl, *args)
        var = ctypes.CVar('check'.format(n.value.id))
        ty = ctypes.ctype_match(var, n.type, ctbl)
        n.retic_ctype = ty
        if isinstance(n.value, ast.Name):
            fvar = ctypes.CVar('checked<{}>'.format(n.value.id))
            env[n.value.id] = fvar
        else:
            fvar = ctypes.CVar('checked')
        return st | {CheckC(n.value.retic_ctype, n.type, ty), EqC(var, n.value.retic_ctype), STC(ty, fvar)}
