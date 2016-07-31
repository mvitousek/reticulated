## The main module for transient check insertion. This relies on
## .retic_type nodes having been inserted by typecheck.py.


from . import copy_visitor, typing, typeparser, retic_ast, ast_trans, flags, exc
import ast

def generateArgumentProtectors(n: ast.arguments, lineno: int, col_offset:int)->typing.List[ast.Expr]:
    ## Given a set of arguments from a FunctionDef, generate the
    ## checks that need to be inserted at function entry in order to
    ## detect incorrect argument values.
    prots = []
    for arg in n.args:
        prots.append(ast.Expr(value=retic_ast.Check(value=ast.Name(id=arg.arg,
                                                                   ctx=ast.Load(), lineno=lineno, col_offset=col_offset),
                                                    type=arg.retic_type, lineno=lineno, col_offset=col_offset),
                              lineno=lineno, col_offset=col_offset))
    for arg in n.kwonlyargs:
        prots.append(ast.Expr(value=retic_ast.Check(value=ast.Name(id=arg.arg,
                                                                   ctx=ast.Load(), lineno=lineno, col_offset=col_offset),
                                                    type=arg.retic_type, lineno=lineno, col_offset=col_offset),
                              lineno=lineno, col_offset=col_offset))
    if n.vararg:
        prots.append(ast.Expr(value=retic_ast.Check(value=ast.Name(id=n.vararg.arg,
                                                                   ctx=ast.Load(), lineno=lineno, col_offset=col_offset),
                                                    type=n.vararg.retic_type, lineno=lineno,
                                                    col_offset=col_offset), lineno=lineno, col_offset=col_offset))
    if n.kwarg:
        prots.append(ast.Expr(value=retic_ast.Check(value=ast.Name(id=n.kwarg.arg,
                                                                   ctx=ast.Load(), lineno=lineno, col_offset=col_offset),
                                                    type=n.kwarg.retic_type, lineno=lineno,
                                                    col_offset=col_offset), lineno=lineno, col_offset=col_offset))
    return prots



class CheckInserter(copy_visitor.CopyVisitor):
    ## The main visitor. Outputs an AST with checks inserted. Here
    ## we're blindly inserting checks wherever they might possibly be
    ## needed, and will rely on other passes to remove extraneous ones
    ## (like where a value is being checked against Dyn)

    ## Usage: CheckInserter().preorder(ast)
    
    
    def visitFunctionDef(self, n, *args):
        fargs = self.dispatch(n.args, *args)
        decorator_list = [self.dispatch(dec, *args) for dec in n.decorator_list]
        body = self.dispatch_scope(n.body, *args)
        arg_protectors = generateArgumentProtectors(n.args, n.lineno, n.col_offset)
        return ast_trans.FunctionDef(name=n.name, args=fargs,
                                     body=arg_protectors+body, decorator_list=decorator_list,
                                     returns=n.returns, 
                                     lineno=n.lineno, col_offset=n.col_offset)

    def visitCall(self, n, *args):
        call =  ast_trans.Call(func=self.dispatch(n.func, *args),
                               args=self.reduce(n.args, *args),
                               keywords=[ast.keyword(arg=k.arg, value=self.dispatch(k.value, *args))\
                                         for k in n.keywords],
                               starargs=self.dispatch(n.starargs, *args) if getattr(n, 'starargs', None) else None,
                               kwargs=self.dispatch(n.kwargs, *args) if getattr(n, 'kwargs', None) else None,
                               lineno=n.lineno, col_offset=n.col_offset)
        return retic_ast.Check(value=call, type=n.retic_type, lineno=n.lineno, col_offset=n.col_offset)
        
    def visitAttribute(self, n, *args):
        attr = ast.Attribute(value=self.dispatch(n.value, *args),
                             attr=n.attr, ctx=n.ctx,
                             lineno=n.lineno, col_offset=n.col_offset)
        return retic_ast.Check(value=attr, type=n.retic_type, lineno=n.lineno, col_offset=n.col_offset)
        
    def visitSubscript(self, n, *args):
        value = self.dispatch(n.value, *args)
        slice = self.dispatch(n.slice, *args)
        return retic_ast.Check(value=ast.Subscript(value=value, slice=slice, ctx=n.ctx, lineno=n.lineno, col_offset=n.col_offset),
                               type=n.retic_type, lineno=n.lineno, col_offset=n.col_offset)
        
    def visitFor(self, n, *args):
        # We need to guard the internal body of for loops to make sure that the iteration target has the expected type.

        # Currently this only works for things like 'for x in ...', and will fail for 'for x,y in ...' or 'for a.b in ...'!
        prot = ast.Expr(value=retic_ast.Check(value=ast.Name(id=n.target.id, ctx=ast.Load(),
                                                             lineno=n.lineno, col_offset=n.col_offset),
                                              type=n.target.retic_type, lineno=n.lineno, col_offset=n.col_offset), lineno=n.lineno, col_offset=n.col_offset)
        return ast.For(target=self.dispatch(n.target, *args),
                       iter=self.dispatch(n.iter, *args),
                       body=[prot] + self.dispatch_statements(n.body, *args),
                       orelse=self.dispatch_statements(n.orelse, *args),
                       lineno=n.lineno, col_offset=n.col_offset)

    def visitAssign(self, n, *args):
        value = self.dispatch(n.value, *args)
        prots = []
        
        for target in n.targets:
            # Don't recur on the targets since we can never have a LHS check
            
            # Need to insert a check for each variable target (inc decomposed variable targets UNIMPLEMENTED)
            #
            # So, if our statement is 
            #  x = y = z
            # We need to ensure that z has the types of x and y.
            # However, for non-variables, we don't need to worry:
            #  x[0] = y.a = z
            # No checks needed here, because checks will be used at dereferences.
            # For destructuring assignment we get weirder. Say we have
            #  x, y = z 
            # with x:int, y:str, z:dyn.
            # We can also have starred assignment.
            #  x, *y, z = w
            # with x:int, y:List[str], z:int, w:dyn
            # To handle these things, we generate a list of checks and
            # put them in an ExpandSeq node, which sequences
            # statements.
            def destruct_to_checks(lhs: ast.expr):
                if isinstance(lhs, ast.Name):
                    return [ast.Expr(value=retic_ast.Check(value=ast.Name(id=lhs.id, 
                                                                          ctx=ast.Load(), lineno=lhs.lineno, col_offset=lhs.col_offset), 
                                                           type=lhs.retic_type, lineno=lhs.lineno, col_offset=lhs.col_offset),
                                     lineno=lhs.lineno, col_offset=lhs.col_offset)]
                elif isinstance(lhs, ast.Tuple) or isinstance(lhs, ast.List):
                    return sum((destruct_to_checks(targ) for targ in lhs.elts), [])
                elif isinstance(lhs, ast.Starred):
                    return destruct_to_checks(lhs.value)
                elif isinstance(lhs, ast.Attribute) or isinstance(lhs, ast.Subscript):
                    return []
                else: 
                    raise exc.InternalReticulatedError(lhs)

            
            # If the target is a single assignment, let's just put the check on the RHS.
            # If it's something more complicated, leave the check till after the assignment
            if isinstance(target, ast.Name):
                value = retic_ast.Check(value=value, type=target.retic_type, lineno=value.lineno, col_offset=value.col_offset)
            else:
                prots += destruct_to_checks(target)
                
            return retic_ast.ExpandSeq(body=[ast.Assign(targets=n.targets, value=value, lineno=n.lineno, col_offset=n.col_offset)] + prots,
                                       lineno=value.lineno, col_offset=value.col_offset)


    # ExceptionHandlers should have a retic_type node for the type of
    # the bound variable, if it exists. We need to guard the inside of
    # the exceptionhandler from bad bindings: like if the binder x has
    # type MyException, and the .type field (representing the kind of
    # exceptions caught) has Retic type Dyn, but is at runtime a
    # NotMyException
    def visitExceptHandler(self, n, *args):
        type = self.dispatch(n.type, *args)
        body = self.dispatch(n.body, *args)
        
        if n.name:
            prot = ast.Expr(value=retic_ast.Check(value=ast.Name(id=n.name, ctx=ast.Load(),
                                                                 lineno=n.lineno, col_offset=n.col_offset),
                                                  type=n.retic_type, lineno=n.lineno, col_offset=n.col_offset), lineno=n.lineno, col_offset=n.col_offset)
            body = [prot] + body
            
        return ast.ExceptHandler(name=n.name, type=type, body=body)

    # Logic used in < 3.2 as part of With and > 3.2 in withitem:
    def handlewithitem(self, optvars):
        # See visitAssign for what checks we have to add when.
        if optvars:
            if isinstance(optvars, ast.Name):
                return ast.Expr(value=retic_ast.Check(value=ast.Name(id=optvars.id, ctx=ast.Load(),
                                                                     lineno=optvars.lineno, col_offset=optvars.col_offset),
                                                      type=optvars.retic_type, lineno=optvars.lineno, col_offset=optvars.col_offset), 
                                lineno=optvars.lineno, col_offset=optvars.col_offset)
            elif isinstance(target, ast.Starred):
                raise exc.UnimplementedException('Assignment checks against Starred')
            elif isinstance(target, ast.List):
                raise exc.UnimplementedException('Assignment checks against List')
            elif isinstance(target, ast.Tuple):
                raise exc.UnimplementedException('Assignment checks against Tuple')
        return None
        
    # We need to propagate checks back to the ast.With, since the body
    # (where the checks would be used) is not included in a
    # withitem. Therefore, we stick them on the resulting withitem.
    def visitwithitem(self, n, *args):
        cexpr = self.dispatch(n.context_expr, *args)
        optvars = self.dispatch(n.optional_vars, *args)

        prot = self.handlewithitem(optvars)

        ret = ast.withitem(context_expr=cexpr, optional_vars=optvars)
        ret.retic_protector = prot
        return ret

    # As discussed in visitwithitem, withitems can't directly produce
    # checks in the body of the with. So we extract them from the withitems.
    def visitWith(self, n, *args):
        body = self.dispatch(n.body, *args)
        if flags.PY_VERSION == 3 and flags.PY3_VERSION >= 3:
            items = [self.dispatch(item, *args) for item in n.items]
            prots = [itm.retic_protector for itm in items if itm.retic_protector]
            return ast.With(items=items, body=prots + body)
        else:
            cexpr = self.dispatch(n.context_expr, *args)
            optvars = self.dispatch(n.optional_vars, *args)

            prot = self.handlewithitem(optvars)
            if prot:
                body = [prot] + body
                
            return ast.With(context_expr=cexpr, optional_vars=optvars, body=body)
            
        


    # Missing comprehension stuff. We need to treat it sort of like
    # decompositing assignment, since we can have assignment patterns
    # as targets of comprehensions.
    
        
