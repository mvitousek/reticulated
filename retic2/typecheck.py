from . import scope, typeparser, exc, vis, flags, retic_ast, consistency

class Typechecker(vis.Visitor):
    # Detects static type errors and _UPDATES IN PLACE_ the ast. Each expression node should have a .retic_type node added

    def visitlist(self, n, *args):
        for s in n:
            self.dispatch(s, *args)
        
    def visitNoneType(self, n, *args): pass

    def visitModule(self, n):
        env = scope.getModuleScope(n)
        self.dispatch(n.body, env)

    def visitFunctionDef(self, n, env, *args):
        self.dispatch(n.args, env, *args)
        [self.dispatch(dec, env, *args) for dec in n.decorator_list]

        fun_env = scope.getFunctionScope(n, env)
        # Attaching return type to 
        n.retic_return_type = typeparser.typeparse(n.returns)

        self.dispatch(n.body, fun_env, *args)
        

    def visitarguments(self, n, *args):
        # Need to check the types of default arguments against their annotations
        [self.dispatch(default, *args) for default in n.defaults]
        [self.dispatch(arg, *args) for arg in n.args]
        if flags.PY_VERSION == 3:
            [self.dispatch(default, *args) for default in n.kw_defaults]

    def visitarg(self, n, *args):
        self.dispatch(n.annotation, *args)

    def visitReturn(self, n, *args):
        # Handle return type checking in a separate pass
        self.dispatch(n.value, *args)

    # Assignment stuff
    def visitAssign(self, n, *args):
        self.dispatch(n.value, *args)
        for target in n.targets:
            self.dispatch(target, *args)
            if isinstance(target, ast.Name):
                if not consistency.assignable(target.retic_type, n.value.retic_type):
                    raise exc.StaticTypeError(target, 'Value of type {} cannot be assigned to variable {}, which has type {}'.format(n.value.retic_type, target.id, target.retic_type))
            else:
                raise exc.UnimplementedException()

    def visitAugAssign(self, n, *args):
        self.dispatch(n.value, *args)
        self.dispatch(n.target, *args)
        ty = consistency.apply_binop(n.op, n.target.retic_type, n.value.retic_type)
        if not consistency.assignable(n.target.retic_type, ty):
            raise exc.StaticTypeError(n.value, 'Value of type {} cannot be {} into a target which has type {}'.format(n.value.retic_type, 
                                                                                                                      stringify(n.op, 'PASTTENSE'), 
                                                                                                                      target.id, target.retic_type))

    def visitDelete(self, n, *args):
        [self.dispatch(target,*args) for target in n.targets]
        for target in n.targets:
            self.dispatch(target, *args)
            if not isinstance(target.retic_type, retic_ast.Dyn):
                raise exc.StaticTypeError(target, 'Statically typed values cannot be deleted')

    # Control flow stuff
    def visitIf(self, n, *args):
        self.dispatch(n.test, *args)
        if not consistency.assignable(retic_ast.Bool(), n.test.retic_type):
            raise exc.StaticTypeError(n.test, 'Test expression has type {} but was expected to have type bool'.format(n.test.retic_type))
        self.dispatch(n.body, *args)
        self.dispatch(n.orelse, *args)

    def visitFor(self, n, *args):
        self.dispatch(n.target, *args)
        self.dispatch(n.iter, *args)
        if not consistency.members_assignable(n.target.retic_type, n.iter.retic_type):
            raise exc.StaticTypeError(n.target, 'Iteration expression has type {}, but the iteration variable(s) have the expected type {}'.format(n.iter.retic_type, n.target.retic_type))
        self.dispatch(n.body, *args)
        self.dispatch(n.orelse, *args)

    def visitWhile(self, n, *args):
        self.dispatch(n.test, *args)
        if not consistency.assignable(retic_ast.Bool(), n.test.retic_type):
            raise exc.StaticTypeError(n.test, 'Test expression has type {} but was expected to have type bool'.format(n.test.retic_type))
        self.dispatch(n.body, *args)
        self.dispatch(n.orelse, *args)

    def visitWith(self, n, *args): # NOT FULLY INVESTIGATED
        # old retic didn't reject anything from a with but 
        # we should investigate if there's anything to do here
        self.dispatch(n.body, *args)
        if flags.PY_VERSION == 3 and flags.PY3_VERSION >= 3:
            [self.dispatch(item, *args) for item in n.items]
        else:
            self.dispatch(n.context_expr, *args)
            self.dispatch(n.optional_vars, *args)

    def visitwithitem(self, n, *args):
        self.dispatch(n.context_expr, *args)
        self.dispatch(n.optional_vars, *args)
            

    # Class stuff
    def visitClassDef(self, n, *args):
        raise exc.UnimplementedException()
            

    # Exception stuff
    # Python 2.7, 3.2
    def visitTryExcept(self, n, *args):
        self.dispatch(n.body, *args)
        self.dispatch(n.handlers, *args)
        self.dispatch(n.orelse, *args)

    # Python 2.7, 3.2
    def visitTryFinally(self, n, *args):
        self.dispatch(n.body, *args)
        self.dispatch(n.finalbody, *args)
    
    # Python 3.3
    def visitTry(self, n, *args):
        self.dispatch(n.body, *args)
        self.dispatch(n.handlers, *args)
        self.dispatch(n.orelse, *args)
        self.dispatch(n.finalbody, *args)

    def visitExceptHandler(self, n, *args):
        self.dispatch(n.type, *args)
        self.dispatch(n.body, *args)

    def visitRaise(self, n, *args):
        if flags.PY_VERSION == 3:
            self.dispatch(n.exc, *args)
            self.dispatch(n.cause, *args)
        elif flags.PY_VERSION == 2:
            self.dispatch(n.type, *args)
            self.dispatch(n.inst, *args)
            self.dispatch(n.tback, *args)

    def visitAssert(self, n, *args):
        self.dispatch(n.test, *args)
        if not consistency.assignable(retic_ast.Bool(), n.test.retic_type):
            raise exc.StaticTypeError(n.test, 'Asserted expression has type {} but was expected to have type bool'.format(n.test.retic_type))
        self.dispatch(n.msg, *args)

    # Miscellaneous
    def visitExpr(self, n, *args):
        self.dispatch(n.value, *args)

    def visitPrint(self, n, *args):
        self.dispatch(n.dest, *args)
        self.dispatch(n.values, *args)

    def visitExec(self, n, *args):
        self.dispatch(n.body, *args)
        self.dispatch(n.globals, *args) 
        self.dispatch(n.locals, *args)

    def visitImport(self, n, *args): pass
    def visitImportFrom(self, n, *args): pass
    def visitPass(self, n, *args): pass
    def visitBreak(self, n, *args): pass
    def visitContinue(self, n, *args): pass

### EXPRESSIONS ###
    # Op stuff
    def visitBoolOp(self, n, *args):
        tys = []
        for val in n.values:
            self.dispatch(val, *args)
            tys.append(val.retic_type)
        n.retic_type = consistency.join(*tys)

    def visitBinOp(self, n, *args):
        self.dispatch(n.left, *args)
        self.dispatch(n.right, *args)
        ty = consistency.apply_binop(n.op, n.left.retic_type, n.right.retic_type)
        if ty:
            n.retic_type = ty
        else: raise StaticTypeError(n, 'Can\'t {} operands of type {} and {}'.format(stringify(n.op), n.left.retic_type, n.right.retic_type))

    def visitUnaryOp(self, n, *args):
        self.dispatch(n.operand, *args)
        ty = consistency.apply_unop(n.op, n.operand.retic_type)
        if ty:
            n.retic_type = ty
        else: raise StaticTypeError(n, 'Can\'t {} an operand of type {}'.format(stringify(n.op), n.operand.retic_type))

    def visitCompare(self, n, *args):
        self.dispatch(n.left, *args)
        self.dispatch(n.comparators, *args)
        # Some rather complicated logic needed here to reject objects that definitely don't have __lt__ etc
        n.retic_type = retic_ast.Bool()
        
    # Collections stuff    
    def visitList(self, n, *args):
        tys = []
        for val in n.elts:
            self.dispatch(val, *args)
            tys.append(val.retic_type)
        n.retic_type = retic_ast.List(consistency.join(*tys))

    def visitTuple(self, n, *args):
        tys = []
        for val in n.elts:
            self.dispatch(val, *args)
            tys.append(val.retic_type)
        n.retic_type = retic_ast.Dyn() # Add tuple types

    def visitDict(self, n, *args):
        ktys = []
        vtys = []
        for key in n.keys:
            self.dispatch(key, *args)
            ktys.append(key.retic_type)
        for val in n.values:
            self.dispatch(val, *args)
            vtys.append(val.retic_type)
        n.retic_type = retic_ast.Dyn() # Add dict types

    def visitSet(self, n, *args):
        tys = []
        for val in n.elts:
            self.dispatch(val, *args)
            tys.append(val.retic_type)
        n.retic_type = retic_ast.Dyn() # Add set tys

    def visitListComp(self, n,*args):
        self.dispatch(n.generators, *args)
        self.dispatch(n.elt, *args)
        n.retic_type = retic_ast.List(retic_ast.Dyn())

    def visitSetComp(self, n, *args):
        self.dispatch(n.generators, *args)
        self.dispatch(n.elt, *args)
        n.retic_type = retic_ast.Dyn()

    def visitDictComp(self, n, *args):
        self.dispatch(n.generators, *args)
        self.dispatch(n.key, *args)
        self.dispatch(n.value, *args)
        n.retic_type = retic_ast.Dyn()

    def visitGeneratorExp(self, n, *args):
        self.dispatch(n.generators, *args)
        self.dispatch(n.elt, *args)
        n.retic_type = retic_ast.Dyn()

    def visitcomprehension(self, n, *args):
        self.dispatch(n.iter, *args)
        self.dispatch(n.ifs, *args)
        self.dispatch(n.target, *args)

    # Control flow stuff
    def visitYield(self, n, *args):
        self.dispatch(n.value, *args)
        n.retic_type = retic_ast.Dyn()

    def visitYieldFrom(self, n, *args):
        self.dispatch(n.value, *args)
        n.retic_type = retic_ast.Dyn()

    def visitIfExp(self, n, *args):
        self.dispatch(n.test, *args)
        if not consistency.assignable(retic_ast.Bool(), n.test.retic_type):
            raise exc.StaticTypeError(n.test, 'Test expression has type {} but was expected to have type bool'.format(n.test.retic_type))
        self.dispatch(n.body, *args)
        self.dispatch(n.orelse, *args)
        n.retic_type = consistency.join(n.body.retic_type, n.orelse.retic_type)

    # Function stuff
    def visitCall(self, n, *args):
        self.dispatch(n.func, *args)
        self.dispatch(n.args, *args)
        [ast.keyword(arg=k.arg, value=self.dispatch(k.value, *args)) for k in n.keywords]
        self.dispatch(n.starargs, *args) if getattr(n, 'starargs', None) else None
        self.dispatch(n.kwargs, *args) if getattr(n, 'kwargs', None) else None
        
        ty, tyerr = consistency.apply(n.func, n.func.retic_type, n.args, n.keywords, n.starargs, n.kwargs)
        if not ty:
            raise tyerr
        else: n.retic_type = ty

    def visitLambda(self, n, env, *args):
        self.dispatch(n.args, env, *args)
        lam_env = scope.getLambdaScope(n, env)
        self.dispatch(n.body, lam_env, *args)

        argtys = []
        for arg in n.args.args:
            if arg.annotation:
                argty = typeparser.typeparse(arg.annotation)
            else:
                argty = retic_ast.Dyn()
            argtys.append(argty)
        retty = n.body.retic_type

        n.retic_type = retic_ast.Function(retic_ast.PosAT(argtys), retty)

    # Variable stuff
    def visitAttribute(self, n, *args):
        self.dispatch(n.value, *args)
        n.retic_type = retic_ast.Dyn()

    def visitSubscript(self, n, *args):
        self.dispatch(n.value, *args)
        self.dispatch(n.slice, *args)
        n.retic_type = retic_ast.Dyn()

    def visitIndex(self, n, *args):
        self.dispatch(n.value, *args)
        n.retic_type = retic_ast.Dyn()

    def visitSlice(self, n, *args):
        self.dispatch(n.lower, *args)
        self.dispatch(n.upper, *args)
        self.dispatch(n.step, *args)
        n.retic_type = retic_ast.Dyn()

    def visitExtSlice(self, n, *args):
        self.dispatch(n.dims, *args)
        n.retic_type = retic_ast.Dyn()

    def visitStarred(self, n, *args):
        self.dispatch(n.value, env)
        n.retic_type = retic_ast.Dyn()

    def visitNameConstant(self, n, *args):
        if n.value is True or n.value is False:
            n.retic_type = retic_ast.Bool()
        elif n.value is None:
            n.retic_type = retic_ast.Void() 
        else: n.retic_type = retic_ast.Dyn()

    def visitName(self, n, env, *args):
        if n.id in env:
            n.retic_type = env[n.id]
        else:
            n.retic_type = retic_ast.Dyn()

    def visitNum(self, n, *args):
        if isinstance(n.n, int):
            n.retic_type = retic_ast.Int()
        else:
            n.retic_type = retic_ast.Dyn()

    def visitStr(self, n, *args):
        n.retic_type = retic_ast.Str()

    def visitBytes(self, n, *args):
        n.retic_type = retic_ast.Dyn()

    def visitEllipsis(self, n, *args):
        n.retic_type = retic_ast.Dyn()
    
    def visitGlobal(self, n, *args): pass
    def visitNonlocal(self, n, *args): pass

