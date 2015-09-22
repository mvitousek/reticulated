from . import typing, reflection, typecheck, flags
from .typecheck import Typechecker, fixup, cast, error
from .relations import *
from .rtypes import *
from .errors import errmsg
from .typing import *
from .gatherers import FallOffVisitor, WILL_RETURN

def check(val, action, args, trg, msg, check_function='retic_mgd_check'):
    msg = '\n' + msg
    if flags.SEMI_DRY:
        return val
    if flags.SQUELCH_MESSAGES:
        msg = ''
    assert hasattr(val, 'lineno')
    lineno = str(val.lineno)
    
    if not tyinstance(trg, Dyn) or not flags.OPTIMIZED_INSERTION:
        logging.warn('Inserting check at line %s: %s' % (lineno, trg), 2)
        return fixup(ast.Call(func=ast.Name(id=check_function, ctx=ast.Load()),
                              args=[val, ast.Str(s=action), ast.List(elts=args, ctx=ast.Load(), lineno=val.lineno),
                                    trg.to_ast(), ast.Str(s=msg)],
                              keywords=[], starargs=None, kwargs=None), val.lineno)
    else: return val


# Check, but within an expression statement
def check_stmtlist(val, action, args, trg, msg, check_function='retic_mgd_check', lineno=None):
    if flags.SEMI_DRY:
        return []
    assert hasattr(val, 'lineno'), ast.dump(val)
    chkval = check(val, action, args, trg, msg, check_function)
    if not flags.OPTIMIZED_INSERTION:
        return [ast.Expr(value=chkval, lineno=val.lineno)]
    else:
        if flags.SEMANTICS not in ['TRANS', 'MGDTRANS'] or chkval == val or tyinstance(trg, Dyn):
            return []
        else: return [ast.Expr(value=chkval, lineno=val.lineno)]

class ManagedTypechecker(Typechecker):
    def visitAttribute(self, n, env, misc):
        value, vty = self.dispatch(n.value, env, misc)

        if tyinstance(vty, InferBottom):
            return n, Dyn

        if isinstance(vty, Structural) and isinstance(n.ctx, ast.Load):
            vty = vty.structure()
        assert vty is not None, n.value

        if tyinstance(vty, Self):
            try:
                ty = misc.cls.instance().member_type(n.attr)
            except KeyError:
                if flags.CHECK_ACCESS and not flags.CLOSED_CLASSES and not isinstance(n.ctx, ast.Store):
                    value = cast(env, misc.cls, value, misc.cls.instance(), Object(misc.cls.name, {n.attr: Dyn}), 
                                 errmsg('WIDTH_DOWNCAST', misc.filename, n, n.attr))
                ty = Dyn
            if isinstance(value, ast.Name) and value.id == misc.receiver.id:
                if flags.SEMANTICS == 'MONO' and not isinstance(n.ctx, ast.Store) and not isinstance(n.ctx, ast.Del) and \
                        not tyinstance(ty, Dyn):
                    ans = ast.Call(func=ast.Name(id='retic_getattr_'+('static' if ty.static() else 'dynamic'), 
                                                 ctx=ast.Load(), lineno=n.lineno),
                                   args=[value, ast.Str(s=n.attr), ty.to_ast()],
                                   keywords=[], starargs=None, kwargs=None, lineno=n.lineno)
                    return ans, ty
                else: return ast.Attribute(value=value, attr=n.attr, lineno=n.lineno, ctx=n.ctx), ty
            if isinstance(n.ctx, ast.Store):
                return ast.Attribute(value=value, attr=n.attr, lineno=n.lineno, ctx=n.ctx), ty
            return ast.Call(func=ast.Name(id='retic_bindmethod', ctx=ast.Load()),
                            args=[ast.Attribute(value=misc.receiver, attr='__class__', ctx=ast.Load()),
                                  value, ast.Str(s=n.attr)], keywords=[], starargs=None, kwargs=None, 
                            lineno=n.lineno), \
                                  ty
        elif tyinstance(vty, Object) or tyinstance(vty, Class):
            try:
                ty = vty.member_type(n.attr)
                if isinstance(n.ctx, ast.Del):
                    return error(errmsg('TYPED_ATTR_DELETE', misc.filename, n, n.attr, ty), lineno=n.lineno), Dyn
            except KeyError:
                if flags.CHECK_ACCESS and not flags.CLOSED_CLASSES and not isinstance(n.ctx, ast.Store):
                    value = cast(env, misc.cls, value, vty, vty.__class__('', {n.attr: Dyn}), 
                                 errmsg('WIDTH_DOWNCAST', misc.filename, n, n.attr))
                ty = Dyn
        elif tyinstance(vty, Dyn):
            if flags.CHECK_ACCESS and not isinstance(n.ctx, ast.Store) and not isinstance(n.ctx, ast.Del):
                value = cast(env, misc.cls, value, vty, Record({n.attr: Dyn}), 
                             errmsg('WIDTH_DOWNCAST', misc.filename, n, n.attr)) 
            else:
                value = cast(env, misc.cls, value, vty, Record({}), 
                             errmsg('NON_OBJECT_' + ('WRITE' if isinstance(n.ctx, ast.Store) \
                                                         else 'DEL'), misc.filename, n, n.attr))
            ty = Dyn
        else: 
            kind = 'WRITE' if isinstance(n.ctx, ast.Store) else ('DEL' if isinstance(n.ctx, ast.Del) else 'READ')
            return error(errmsg('NON_OBJECT_' + kind, misc.filename, n, n.attr) % static_val(vty), lineno=n.lineno), Dyn

        if flags.SEMANTICS == 'MONO' and not isinstance(n.ctx, ast.Store) and not isinstance(n.ctx, ast.Del) and \
                not tyinstance(ty, Dyn):
            ans = ast.Call(func=ast.Name(id='retic_getattr_'+('static' if ty.static() else 'dynamic'), 
                                         ctx=ast.Load(), lineno=n.lineno),
                           args=[value, ast.Str(s=n.attr), ty.to_ast()],
                        keywords=[], starargs=None, kwargs=None, lineno=n.lineno)
            return ans, ty

        ans = ast.Attribute(value=value, attr=n.attr, ctx=n.ctx, lineno=n.lineno)
        if not isinstance(n.ctx, ast.Store) and not isinstance(n.ctx, ast.Del):
            ans = check(value, 'GETATTR', [ast.Str(s=n.attr)], ty, errmsg('ACCESS_CHECK', misc.filename, n, n.attr, ty))
        return ans, ty

    def visitSubscript(self, n, env, misc):
        value, vty = self.dispatch(n.value, env, misc)
        if tyinstance(vty, InferBottom):
            return n, Dyn
        slice, ty = self.dispatch(n.slice, env, vty, misc, n.lineno)
        ans = ast.Subscript(value=value, slice=slice, ctx=n.ctx, lineno=n.lineno)
        if not isinstance(n.ctx, ast.Store):
            ans = check(ans, 'GETITEM', [value], ty, errmsg('SUBSCRIPT_CHECK', misc.filename, n, ty))
        return ans, ty

    # Function stuff
    def visitCall(self, n, env, misc):
        if reflection.is_reflective(n):
            return reflection.reflect(n, env, misc, self)

        project_needed = [False] # Python2 doesn't have nonlocal
        class BadCall(Exception):
            def __init__(self, msg):
                self.msg = msg
        def cast_args(argdata, fun, funty):
            vs, ss = zip(*argdata) if argdata else ([], [])
            vs = list(vs)
            ss = list(ss)
            if tyinstance(funty, Dyn):
                if n.keywords or n.starargs or n.kwargs:
                    targparams = DynParameters
                else: targparams = AnonymousParameters(ss)
                return vs, cast(env, misc.cls, fun, Dyn, Function(targparams, Dyn),
                                errmsg('FUNC_ERROR', misc.filename, n, Function(targparams, Dyn))), Dyn
            elif tyinstance(funty, Function):
                argcasts = funty.froms.lenmatch(argdata)
                # Prototype implementation for type variables

                if argcasts != None:
                    substs = []
                    casts = []
                    for (v, s), t in argcasts:
                        if isinstance(t, TypeVariable):
                            substs.append((t.name, s))
                            casts.append(v)
                        else:
                            casts.append(cast(env, misc.cls, v, s, t, errmsg('ARG_ERROR', misc.filename, n, t)))
                    to = funty.to
                    for var,rep in substs:
                        # Still need to merge in case of multiple approaches
                        to = to.substitute(var, rep, False)

                    return(casts, fun, to)

                    # return ([cast(env, misc.cls, v, s, t, errmsg('ARG_ERROR', misc.filename, n, t)) for \
                    #             (v, s), t in argcasts],
                    #         fun, funty.to)
                else: 
                    raise BadCall(errmsg('BAD_ARG_COUNT', misc.filename, n, funty.froms.len(), len(argdata)))
            elif tyinstance(funty, Class):
                project_needed[0] = True
                if '__init__' in funty.members:
                    inst = funty.instance()
                    funty = funty.member_type('__init__')
                    if tyinstance(funty, Function):
                        funty = funty.bind()
                        funty.to = inst
                else:
                    funty = Function(DynParameters, funty.instance())
                return cast_args(argdata, fun, funty)
            elif tyinstance(funty, Object):
                if '__call__' in funty.members:
                    funty = funty.member_type('__call__')
                    return cast_args(argdata, fun, funty)
                else:
                    mfunty = Function(DynParameters, Dyn)
                    return cast_args(argdata, cast(env, misc.cls, fun, funty, Record({'__call__': mfunty}), 
                                                   errmsg('OBJCALL_ERROR', misc.filename, n)),
                                     mfunty)
            else: raise BadCall(errmsg('BAD_CALL', misc.filename, n, funty))

        (func, ty) = self.dispatch(n.func, env, misc)

        if tyinstance(ty, InferBottom):
            return n, Dyn

        argdata = [self.dispatch(x, env, misc) for x in n.args]
        try:
            (args, func, retty) = cast_args(argdata, func, ty)
        except BadCall as e:
            if flags.REJECT_WEIRD_CALLS or not (n.keywords or n.starargs or n.kwargs):
                return error(e.msg, lineno=n.lineno), Dyn
            else:
                logging.warn('Function calls with keywords, starargs, and kwargs are not typechecked. Using them may induce a type error in file %s (line %d)' % (misc.filename, n.lineno), 0)
                args = n.args
                retty = Dyn
        call = ast.Call(func=func, args=args, keywords=n.keywords,
                        starargs=n.starargs, kwargs=n.kwargs, lineno=n.lineno)
        if project_needed[0]:
            call = cast(env, misc.cls, call, Dyn, retty, errmsg('BAD_OBJECT_INJECTION', misc.filename, n, retty, ty))
        else: call = check(call, 'RETURN', [func], retty, errmsg('RETURN_CHECK', misc.filename, n, retty))
        return (call, retty)


    def visitFunctionDef(self, n, env, misc): #TODO: check defaults, handle varargs and kwargs

        try:
            nty = env[Var(n.name)]
        except KeyError as e :
            assert False, ('%s at %s:%d' % (e ,misc.filename, n.lineno))

        if not misc.methodscope and not nty.self_free():
            error(errmsg('UNSCOPED_SELF', misc.filename, n), lineno=n.lineno)

        name = n.name if n.name not in TYPES else n.name + '_'
        assign = ast.Assign(targets=[ast.Name(id=name, ctx=ast.Store(), lineno=n.lineno)], 
                            value=cast(env, misc.cls, ast.Name(id=name, ctx=ast.Load(), lineno=n.lineno), Dyn, nty, errmsg('BAD_FUNCTION_INJECTION', misc.filename, n, nty)),
                            lineno=n.lineno)

        froms = nty.froms if hasattr(nty, 'froms') else DynParameters#[Dyn] * len(argnames)
        to = nty.to if hasattr(nty, 'to') else Dyn

        args, argnames, specials = self.dispatch(n.args, env, froms, misc, n.lineno)
        decorator_list = n.decorator_list#[self.dispatch(dec, env, misc)[0] for dec in n.decorator_list if not is_annotation(dec)]
        # Decorators have a restricted syntax that doesn't allow function calls
        env = (misc.extenv if misc.cls else env).copy()

        if misc.cls:
            receiver = None if (not misc.methodscope or len(argnames) == 0) else\
                ast.Name(id=argnames[0], ctx=ast.Load())
        else: 
            receiver = None


        argtys = froms.lenmatch([Var(x) for x in argnames])
        assert(argtys != None)
        initial_locals = dict(argtys + specials)
        logging.debug('Function %s typechecker starting in %s' % (n.name, misc.filename), flags.PROC)
        body, _ = misc.static.typecheck(n.body, env, initial_locals, typing.Misc(ret=to, cls=misc.cls, receiver=receiver, extenv=misc.extenv, extend=misc))
        logging.debug('Function %s typechecker finished in %s' % (n.name, misc.filename), flags.PROC)
        
        force_checks = tyinstance(froms, DynParameters)

        argchecks = sum((check_stmtlist(ast.Name(id=arg.var, ctx=ast.Load(), lineno=n.lineno), 
                                        'ARG', [ast.Name(id=n.name, ctx=ast.Load()), ast.Num(n=pos)],
                                        ty,
                                        errmsg('ARG_CHECK', misc.filename, n, arg.var, ty),
                                        lineno=n.lineno) for (pos, (arg, ty)) in enumerate(argtys)), [])

        logging.debug('Returns checker starting in %s' % misc.filename, flags.PROC)
        fo = self.falloffvisitor.dispatch_statements(body)
        logging.debug('Returns checker finished in %s' % misc.filename, flags.PROC)
        if to != Dyn and to != Void and fo != WILL_RETURN:
            return error_stmt(errmsg('FALLOFF', misc.filename, n, n.name, to), n.lineno)

        # REMOVED INJECTION FOR TRANSIENT
            
        if flags.PY_VERSION == 3:
            return [ast.FunctionDef(name=name, args=args,
                                     body=argchecks+body, decorator_list=decorator_list,
                                     returns=n.returns, lineno=n.lineno)]
        elif flags.PY_VERSION == 2:
            return [ast.FunctionDef(name=name, args=args,
                                     body=argchecks+body, decorator_list=decorator_list,
                                     lineno=n.lineno)]
