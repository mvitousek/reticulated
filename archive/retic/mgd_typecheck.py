from . import typing, reflection, typecheck, flags, mgd_transient, utils
from .typecheck import Typechecker, fixup, cast, error
from .relations import *
from .rtypes import *
from .errors import errmsg
from .typing import *
from .gatherers import FallOffVisitor, WILL_RETURN

def check(val, elim, act, trg, msg, check_function='retic_mgd_check'):
    msg = '\n' + msg
    if flags.SEMI_DRY:
        return val
    if flags.SQUELCH_MESSAGES:
        msg = ''
    assert hasattr(val, 'lineno')
    lineno = str(val.lineno)

    if not flags.OPTIMIZED_INSERTION:
        logging.warn('Inserting check at line %s: %s' % (lineno, trg), 2)
        return fixup(ast.Call(func=ast.Name(id=check_function, ctx=ast.Load()),
                              args=[val, ast.Str(s=action), ast.List(elts=args, ctx=ast.Load(), lineno=val.lineno),
                                    trg.to_ast(), ast.Str(s=msg)],
                              keywords=[], starargs=None, kwargs=None), val.lineno)
    else:
        if not tyinstance(trg, Dyn):
            args = [val, elim, act]
            cast_function = 'mgd_check_type_'
            if tyinstance(trg, Int):
                cast_function += 'int'
            elif tyinstance(trg, Float):
                cast_function += 'float'
            elif tyinstance(trg, String):
                cast_function += 'string'
            elif tyinstance(trg, List):
                cast_function += 'list'
            elif tyinstance(trg, Complex):
                cast_function += 'complex'
            elif tyinstance(trg, Tuple):
                cast_function += 'tuple'
                args += [ast.Num(n=len(trg.elements))]
            elif tyinstance(trg, Dict):
                cast_function += 'dict'
            elif tyinstance(trg, Bool):
                cast_function += 'bool'
            elif tyinstance(trg, Void):
                cast_function += 'void'
            elif tyinstance(trg, Set):
                cast_function += 'set'
            elif tyinstance(trg, Function):
                cast_function += 'function'
            elif tyinstance(trg, Class):
                cast_function += 'class'
                args += [ast.List(elts=[ast.Str(s=x) for x in trg.members], ctx=ast.Load())]
            elif tyinstance(trg, Object):
                if len(trg.members) == 0:
                    return val
                cast_function += 'object'
                args += [ast.List(elts=[ast.Str(s=x) for x in trg.members], ctx=ast.Load())]
            else:
                raise Exception('unknown type')

            return fixup(ast.Call(func=ast.Name(id=cast_function, ctx=ast.Load()),
                                  args=args, keywords=[], starargs=None, kwargs=None), lineno=val.lineno)
        else: return val


def cast(env, ctx, val, src, trg, msg, cast_function='retic_cast', misc=None):
    if flags.SEMI_DRY:
        return val
    if flags.SQUELCH_MESSAGES:
        msg = ''
    assert hasattr(val, 'lineno'), ast.dump(val)
    lineno = str(val.lineno)
    merged = merge(src, trg)
    if not trg.top_free() or not subcompat(src, trg, env, ctx):
        return error(msg % static_val(src), lineno)
    elif src == merged:
        return val
    elif not flags.OPTIMIZED_INSERTION:
        msg = '\n' + msg
        logging.warn('Inserting cast at line %s: %s => %s' % (lineno, src, trg), 2)
        return fixup(ast.Call(func=ast.Name(id=cast_function, ctx=ast.Load()),
                              args=[val, src.to_ast(), merged.to_ast(), ast.Str(s=msg)],
                              keywords=[], starargs=None, kwargs=None), val.lineno)
    else:
        if tyinstance(trg, Object):
            if len(trg.members) == 0:
                return val
        if misc is not None:
            srckey = 'gensym'+str(misc.gensymmer[0])
            misc.gensymmer[0] += 1
            trgkey = 'gensym'+str(misc.gensymmer[0])
            misc.gensymmer[0] += 1
            srcname = ast.Name(id=srckey, ctx=ast.Load())
            trgname = ast.Name(id=trgkey, ctx=ast.Load())
            misc.typenames[srckey] = src.to_ast() 
            misc.typenames[trgkey] = merged.to_ast() 
        else: 
            srcname = src.to_ast()
            trgname = merged.to_ast()
            
        msg = str(lineno)
        args = [val, srcname, ast.Str(s=msg), trgname]
        cast_function = 'mgd_cast_type_'
        if tyinstance(trg, Dyn):
            cast_function += 'dyn'
        elif tyinstance(trg, Int):
            cast_function += 'int'
        elif tyinstance(trg, Float):
            cast_function += 'float'
        elif tyinstance(trg, String):
            cast_function += 'string'
        elif tyinstance(trg, List):
            cast_function += 'list'
        elif tyinstance(trg, Complex):
            cast_function += 'complex'
        elif tyinstance(trg, Tuple):
            cast_function += 'tuple'
            args += [ast.Num(n=len(trg.elements))]
        elif tyinstance(trg, Dict):
            cast_function += 'dict'
        elif tyinstance(trg, Bool):
            cast_function += 'bool'
        elif tyinstance(trg, Set):
            cast_function += 'set'
        elif tyinstance(trg, Function):
            cast_function += 'function'
        elif tyinstance(trg, Void):
            cast_function += 'void'
        elif tyinstance(trg, Class):
            cast_function += 'class'
            args += [ast.List(elts=[ast.Str(s=x) for x in trg.members], ctx=ast.Load())]
        elif tyinstance(trg, Object):
            cast_function += 'object'
            args += [ast.List(elts=[ast.Str(s=x) for x in trg.members], ctx=ast.Load())]
        else:
            raise Exception('unknown type')

        return fixup(ast.Call(func=ast.Name(id=cast_function, ctx=ast.Load()),
                              args=args, keywords=[], starargs=None, kwargs=None), lineno=val.lineno)

# Check, but within an expression statement
def check_stmtlist(val, elim, act, trg, msg, check_function='retic_mgd_check', lineno=None):
    if flags.SEMI_DRY:
        return []
    assert hasattr(val, 'lineno'), ast.dump(val)
    chkval = check(val, elim, act, trg, msg, check_function)
    if not flags.OPTIMIZED_INSERTION:
        return [ast.Expr(value=chkval, lineno=val.lineno)]
    else:
        if chkval == val or tyinstance(trg, Dyn):
            return []
        else: return [ast.Expr(value=chkval, lineno=val.lineno)]

class ManagedTypechecker(Typechecker):
    def visitModule(self, n, env, misc):
        misc.typenames = {}
        misc.gensymmer = [0]
        body = self.dispatch(n.body, env, misc)
        typenames = []
        for ty in misc.typenames:
            assign = fixup(ast.Assign(targets=[ast.Name(id=ty, ctx=ast.Store())], value=misc.typenames[ty]), lineno=0)
            typenames.append(assign)
        if len(body) > 0 and isinstance(body[0], ast.ImportFrom) and body[0].module == '__future__':
            prebody = [body[0]]
            body = body[1:]
        else:
            prebody = []
        return ast.Module(body=prebody+typenames+body)

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
                                 errmsg('WIDTH_DOWNCAST', misc.filename, n, n.attr), misc=misc)
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
                                 errmsg('WIDTH_DOWNCAST', misc.filename, n, n.attr), misc=misc)
                ty = Dyn
        elif tyinstance(vty, Dyn):
            if flags.CHECK_ACCESS and not isinstance(n.ctx, ast.Store) and not isinstance(n.ctx, ast.Del):
                value = cast(env, misc.cls, value, vty, Record({n.attr: Dyn}), 
                             errmsg('WIDTH_DOWNCAST', misc.filename, n, n.attr), misc=misc) 
            else:
                value = cast(env, misc.cls, value, vty, Record({}), 
                             errmsg('NON_OBJECT_' + ('WRITE' if isinstance(n.ctx, ast.Store) \
                                                         else 'DEL'), misc.filename, n, n.attr), misc=misc)
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
            ans = check(ans, value, ast.parse('(%d, \'%s\')' % (mgd_transient.GETATTR, n.attr)).body[0].value,
                        ty, errmsg('ACCESS_CHECK', misc.filename, n, n.attr, ty))
        return ans, ty

    def visitSubscript(self, n, env, misc):
        value, vty = self.dispatch(n.value, env, misc)
        if tyinstance(vty, InferBottom):
            return n, Dyn
        slice, ty = self.dispatch(n.slice, env, vty, misc, n.lineno)
        ans = ast.Subscript(value=value, slice=slice, ctx=n.ctx, lineno=n.lineno)
        if not isinstance(n.ctx, ast.Store):
            ans = check(ans, value, ast.parse(str(mgd_transient.GETITEM)).body[0].value, ty, errmsg('SUBSCRIPT_CHECK', misc.filename, n, ty))
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
                                errmsg('FUNC_ERROR', misc.filename, n, Function(targparams, Dyn)), misc=misc), Dyn
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
                            casts.append(cast(env, misc.cls, v, s, t, errmsg('ARG_ERROR', misc.filename, n, t), misc=misc))
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
                                                   errmsg('OBJCALL_ERROR', misc.filename, n), misc=misc),
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
        call = check(call, func, ast.parse(str(mgd_transient.RET)).body[0].value, retty, errmsg('RETURN_CHECK', misc.filename, n, retty))
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
                            value=cast(env, misc.cls, ast.Name(id=name, ctx=ast.Load(), lineno=n.lineno), Dyn, nty, errmsg('BAD_FUNCTION_INJECTION', misc.filename, n, nty), misc=misc),
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
        body, _ = misc.static.typecheck(n.body, env, initial_locals, typing.Misc(ret=to, cls=misc.cls, receiver=receiver, extenv=misc.extenv, extend=misc, gensymmer=misc.gensymmer, typenames=misc.typenames))
        logging.debug('Function %s typechecker finished in %s' % (n.name, misc.filename), flags.PROC)
        
        force_checks = tyinstance(froms, DynParameters)

        if misc.methodscope:
            sf = n.args.args[0].arg
            elim = ast.Attribute(value=ast.Name(id=sf, ctx=ast.Load()), attr=n.name, ctx=ast.Load())
        else:
            elim = ast.Name(id=n.name, ctx=ast.Load())
        argchecks = sum((check_stmtlist(ast.Name(id=arg.var, ctx=ast.Load(), lineno=n.lineno), 
                                        elim,
                                        ast.parse('(%d, %d)' % (mgd_transient.ARG, pos)).body[0].value,
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

    def visitListComp(self, n, env, misc):
        disp = [self.dispatch(generator, env, misc, n.lineno) for generator in n.generators]
        generators, genenv = zip(*disp) if disp else ([], [])
        lenv = env.copy()
        lenv.update(dict(sum(genenv, [])))
        elt, ety = self.dispatch(n.elt, lenv, misc)
        return cast(env, misc.cls, ast.ListComp(elt=elt, generators=list(generators), lineno=n.lineno), 
                    Dyn, List(ety),  errmsg('COMP_CHECK', misc.filename, n, List(ety)), misc=misc), \
            (List(ety) if flags.TYPED_LITERALS else Dyn)

    def visitSetComp(self, n, env, misc):
        disp = [self.dispatch(generator, env, misc, n.lineno) for generator in n.generators]
        generators, genenv = zip(*disp) if disp else ([], [])
        lenv = env.copy()
        lenv.update(dict(sum(genenv, [])))
        elt, ety = self.dispatch(n.elt, lenv, misc)
        return cast(env, misc.cls, ast.SetComp(elt=elt, generators=list(generators), lineno=n.lineno),
                    Dyn, List(ety),  errmsg('COMP_CHECK', misc.filename, n, List(ety)), misc=misc), \
            (Set(ety) if flags.TYPED_LITERALS else Dyn)
    
    def visitDictComp(self, n, env, misc):
        disp = [self.dispatch(generator, env, misc, n.lineno) for generator in n.generators]
        generators, genenv = zip(*disp) if disp else ([], [])
        lenv = env.copy()
        lenv.update(dict(sum(genenv,[])))
        key, kty = self.dispatch(n.key, lenv, misc)
        value, vty = self.dispatch(n.value, lenv, misc)
        return cast(env, misc.cls, ast.DictComp(key=key, value=value, generators=list(generators), lineno=n.lineno), 
                    Dyn, List(ety),  errmsg('COMP_CHECK', misc.filename, n, List(ety)), misc=misc), \
            (Dict(kty, vty) if flags.TYPED_LITERALS else Dyn)

    def visitGeneratorExp(self, n, env, misc):
        disp = [self.dispatch(generator, env, misc, n.lineno) for generator in n.generators]
        generators, genenv = zip(*disp) if disp else ([], [])
        lenv = env.copy()
        lenv.update(dict(sum(genenv, [])))
        elt, ety = self.dispatch(n.elt, lenv, misc)
        return fixup(ast.GeneratorExp(elt=elt, generators=list(generators), lineno=n.lineno)), Dyn

    def visitFor(self, n, env, misc):
        target, tty = self.dispatch(n.target, env, misc)
        iter, ity = self.dispatch(n.iter, env, misc)
        body = self.dispatch(n.body, env, misc)
        orelse = self.dispatch(n.orelse, env, misc) if n.orelse else []
        
        if tyinstance(ity, List):
            iter_ty = List(tty)
        elif tyinstance(ity, Dict):
            iter_ty = Dict(tty, ity.values)
        elif tyinstance(ity, Tuple):
            iter_ty = Tuple(*([tty] * len(ity.elements)))
        else: iter_ty = Dyn

        # IF we don't let-bind the iter, we evaluate it every iteration!!
        let_name = 'gensym' + str(misc.gensymmer[0])
        misc.gensymmer[0] += 1
        bind_iter = fixup(ast.Assign(targets=[ast.Name(id=let_name, ctx=ast.Store())], value=cast(env, misc.cls, iter, ity, iter_ty,
                                                                                                  errmsg('ITER_ERROR', misc.filename, n, iter_ty), 
                                                                                                  misc=misc), lineno=n.lineno))
        targcheck = check_stmtlist(utils.copy_assignee(target, ast.Load()),
                                   ast.Name(id=let_name, ctx=ast.Load()), ast.parse(str(mgd_transient.GETITEM)).body[0].value,
                                   tty, errmsg('ITER_CHECK', misc.filename, n, tty), lineno=n.lineno)

        return [bind_iter, ast.For(target=target, iter=ast.Name(id=let_name, ctx=ast.Load()),
                                   body=targcheck+body, orelse=orelse, lineno=n.lineno)]
