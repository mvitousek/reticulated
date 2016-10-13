## The main module for transient check insertion WITH BLAME and blame-carrying casts. This relies on
## .retic_type nodes having been inserted by typecheck.py.


from . import copy_visitor, typing, typeparser, retic_ast, ast_trans, flags, exc, scope
import ast

def generateArgumentProtectors(responsible: ast.Name, n: ast.arguments, lineno: int, col_offset:int)->typing.List[ast.Expr]:
    ## Given a set of arguments from a FunctionDef, generate the
    ## checks that need to be inserted at function entry in order to
    ## detect incorrect argument values.
    prots = []
    for i, arg in enumerate(n.args):
        prots.append(ast.Expr(value=retic_ast.BlameCheck(value=ast.Name(id=arg.arg,
                                                                        ctx=ast.Load(), lineno=lineno, col_offset=col_offset),
                                                         type=arg.retic_type, responsible=responsible, tag=retic_ast.PosArg(i),
                                                         lineno=lineno, col_offset=col_offset),
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

temp_count = -1
def temp(n):
    global temp_count
    temp_count += 1
    if isinstance(n, ast.Name):
        postfix = n.id
    else: postfix = 'temp'
    return '_retic_{}_{}'.format(temp_count, postfix)
    

def generateTemp(n:ast.expr)->Tuple[ast.Name, ast.stmt]:
    name = temp(n)
    nexp = ast.Name(id=name, ctx=ast.Load(), lineno=n.lineno, col_offset=n.col_offset)
    assgn = ast.Assign(targets=[ast.Name(id=name, ctx=ast.Store(), lineno=n.lineno, col_offset=n.col_offset)],
                       value=n, lineno=n.lineno, col_offset=n.col_offset)
    return nexp, assgn


class CheckInserter(copy_visitor.CopyVisitor):
    ## The main visitor. Outputs an AST with checks inserted. Here
    ## we're blindly inserting checks wherever they might possibly be
    ## needed, and will rely on other passes to remove extraneous ones
    ## (like where a value is being checked against Dyn)

    ## Usage: CheckInserter().preorder(ast)
    
    def visitModule(self, n):
        return ast.Module(body=self.dispatch(n.body, set()))
    
    def visitFunctionDef(self, n, *args):
        fargs = self.dispatch(n.args, *args)
        decorator_list = [self.dispatch(dec, *args) for dec in n.decorator_list]
        body = self.dispatch_scope(n.body, *args)
        responsible = ast.Name(id=n.name, ctx=ast.Load(), lineno=n.lineno, col_offset=n.col_offset)
        arg_protectors = generateArgumentProtectors(responsible, n.args, n.lineno, n.col_offset)
        return ast_trans.FunctionDef(name=n.name, args=fargs,
                                     body=arg_protectors+body, decorator_list=decorator_list,
                                     returns=n.returns, 
                                     lineno=n.lineno, col_offset=n.col_offset)

    def cast_args(self, ftype, pos, kwd, star, kwarg, *args):

        if isinstance(froms, retic_ast.ArbAT):
            pass
        def get_pos(i):
            if isinstance(froms, retic_ast.PosAT):
                assert i < len(froms.types)
                return froms.types[i]
            elif isinstance(froms, retic_ast.NamedAT):
                assert i < len(froms.bindings)
                return froms.bindings[i][1]
            elif isinstance(froms, retic_ast.ApproxNamedAT):
                if i < len(froms.bindings):
                    return froms.bindings[i][1]
                else:
                    return retic_ast.Dyn()
            else: raise exc.InternalReticulatedError()

        def get_named(n):
            if isinstance(froms, retic_ast.NamedAT):
                return dict(froms.bindings[len(pos):])[n]
            elif isinstance(froms, retic_ast.ApproxNamedAT):
                return dict(froms.bindings[len(pos):]).get(n, retic_ast.Dyn())
            else: raise exc.InternalReticulatedError()
            
        # There's implicit unpacking happening here, which I don't
        # know how to deal with for cast propagation.
        if star is not None:
            raise exc.UnimplementedException()
        if kwarg is not None:
            raise exc.UnimplementedException()

        cpos = []

        for i, v in enumerate(pos):
            cpos.append(retic_ast.BlameCast(self.dispatch(v, *args), v.retic_type, get_pos(i), lineno=v.lineno, col_offset=v.col_offset))

        ckwd = []
        for k in kwd:
            ckwd.append(ast.keyword(arg=k.arg, value=retic_ast.BlameCast(self.dispatch(k.value, *args), k.value.retic_type, get_named(k.arg),
                                                                         lineno=v.lineno, col_offset=v.col_offset)))

        return cpos, ckwd, star, kwarg

    def visitCall(self, n, *args):
        responsible, assign = generateTemp(self.dispatch(n.func, *args))
        cargs, keywords, starargs, kwargs = self.cast_args(n.func.retic_type, n.args, n.keywords,
                                                          self.dispatch(n.starargs, *args) if getattr(n, 'starargs', None) else None,
                                                          self.dispatch(n.kwargs, *args) if getattr(n, 'kwargs', None) else None, *args)
        call =  ast_trans.Call(func=responsible,
                               args=cargs,
                               keywords=keywords,
                               starargs=starargs,
                               kwargs=kwargs,
                               lineno=n.lineno, col_offset=n.col_offset)
        return retic_ast.Flattened([assign],
                                   retic_ast.BlameCheck(value=call, type=n.retic_type, responsible=responsible, tag=retic_ast.Ret(), lineno=n.lineno, col_offset=n.col_offset),
                                   lineno=n.lineno, col_offset=n.col_offset)
        
    def visitAttribute(self, n, *args):
        if isinstance(n.ctx, ast.Load):
            responsible, assign = generateTemp(self.dispatch(n.value, *args))
            attr = ast.Attribute(value=responsibe,
                                 attr=n.attr, ctx=n.ctx,
                                 lineno=n.lineno, col_offset=n.col_offset)
            return retic_ast.Flattened([assign], retic_ast.BlameCheck(value=attr, type=n.retic_type, 
                                                                      responsible=responsible, tag=retic_ast.GetAttr(n.attr),
                                                                      lineno=n.lineno, col_offset=n.col_offset),
                                       lineno=n.lineno, col_offset=n.col_offset)
        else: 
            return ast.Attribute(value=self.dispatch(n.value, *args),
                                 attr=n.attr, ctx=n.ctx,
                                 lineno=n.lineno, col_offset=n.col_offset)

    def visitSubscript(self, n, *args):
        value = self.dispatch(n.value, *args)
        slice = self.dispatch(n.slice, *args)
        if isinstance(n.ctx, ast.Load):
            responsible, assign = generateTemp(value)
            sub = ast.Subscript(value=responsible, slice=slice, ctx=n.ctx, lineno=n.lineno, col_offset=n.col_offset)
            return retic_ast.Flattened([assign],
                                       retic_ast.BlameCheck(value=sub, type=n.retic_type, responsible=responsible, tag=retic_ast.GetItem(), 
                                                            lineno=n.lineno, col_offset=n.col_offset), lineno=n.lineno, col_offset=n.col_offset)
        else: 
            return ast.Subscript(value=value, slice=slice, ctx=n.ctx, lineno=n.lineno, col_offset=n.col_offset)

        
    # Need to insert a check for each variable target
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
    def destruct_to_checks(self, lhs: ast.expr, responsible: ast.expr):
        if isinstance(lhs, ast.Name):
            return [ast.Expr(value=retic_ast.BlameCheck(value=ast.Name(id=lhs.id, 
                                                                  ctx=ast.Load(), lineno=lhs.lineno, col_offset=lhs.col_offset), 
                                                        type=lhs.retic_type, responsible=responsible, tag=retic_ast.GetItem(),
                                                        lineno=lhs.lineno, col_offset=lhs.col_offset),
                             lineno=lhs.lineno, col_offset=lhs.col_offset)]
        elif isinstance(lhs, ast.Tuple) or isinstance(lhs, ast.List):
            return sum((self.destruct_to_checks(targ) for targ in lhs.elts), [])
        elif isinstance(lhs, ast.Starred):
            return self.destruct_to_checks(lhs.value)
        elif isinstance(lhs, ast.Attribute) or isinstance(lhs, ast.Subscript):
            return []
        else: 
            raise exc.InternalReticulatedError(lhs)

    def visitFor(self, n, *args):
        # We need to guard the internal body of for loops to make sure that the iteration target has the expected type.

        responsible, assign = generateTemp(self.dispatch(n.iter, *args))
        prots = self.destruct_to_checks(n.target, responsible)
        return ast.ExpandSeq([assign, 
                              ast.For(target=self.dispatch(n.target, *args),
                                      iter=responsible,
                                      body=prots + self.dispatch_statements(n.body, *args),
                                      orelse=self.dispatch_statements(n.orelse, *args),
                                      lineno=n.lineno, col_offset=n.col_offset)],
                             lineno=n.lineno, col_offset=n.col_offset)

    def visitAssign(self, n, *args):
        prots = []
        responsible, assign = generateTemp(self.dispatch(n.value, *args))
        value = responsible

        for target in n.targets:
            # Always cast the RHS. If there's destruction going on, ALSO do the checks. 
            value = retic_ast.BlameCast(value=value, src=n.value.retic_type, trg=target.retic_type, lineno=value.lineno, col_offset=value.col_offset)
            if not isinstance(target, ast.Name):
                prots += self.destruct_to_checks(target, responsible)
                
        return retic_ast.ExpandSeq(body=[ast.Assign(targets=n.targets, value=value, lineno=n.lineno, col_offset=n.col_offset)] + prots,
                                   lineno=value.lineno, col_offset=value.col_offset)


    # Currently this duplicates non-blame functionality, since it's hard to perform a cast here really.
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
            
        
    # Iterate over the comprehensions and produce both the new
    # comprehensions and a new binding for varchecks -- the variables
    # assigned to by the generators
    def handleComprehensions(self, comps, varchecks, *args):
        generators = []
        for comp in comps:
            iter = self.dispatch(comp.iter, varchecks, *args)
            target = self.dispatch(comp.target, varchecks, *args)
            
            vars = scope.WriteTargetFinder().preorder(target)
            varchecks = set.union(vars, varchecks)
            
            ifs = self.dispatch(comp.ifs, varchecks, *args)
            generators.append(ast.comprehension(target=target, iter=iter, ifs=ifs))
        return generators, varchecks

    def visitListComp(self, n, varchecks, *args):
        # In comprehensions, we can't generate protectors to guard
        # arguments since the body is just an expression. Instead we
        # add variables to varchecks to indicate in visitName that the
        # variable should be checked directly. This can lead to
        # duplicated checks but I suspect that's relatively rare.
        
        generators, varchecks = self.handleComprehensions(n.generators, varchecks, *args)
            
        elt = self.dispatch(n.elt, varchecks, *args)
        return ast.ListComp(elt=elt, generators=generators)

    def visitSetComp(self, n, varchecks, *args):
        
        generators, varchecks = self.handleComprehensions(n.generators, varchecks, *args)
            
        elt = self.dispatch(n.elt, varchecks, *args)
        return ast.SetComp(elt=elt, generators=generators)

    def visitDictComp(self, n, varchecks, *args):
        
        generators, varchecks = self.handleComprehensions(n.generators, varchecks, *args)
            
        key = self.dispatch(n.key, varchecks, *args)
        value = self.dispatch(n.value, varchecks, *args)
        return ast.DictComp(key=key, value=value, generators=generators)

    def visitGeneratorExp(self, n, varchecks, *args):
        
        generators, varchecks = self.handleComprehensions(n.generators, varchecks, *args)
            
        elt = self.dispatch(n.elt, varchecks, *args)
        return ast.GeneratorExp(elt=elt, generators=generators)
        
    def visitcomprehension(self, n, *args):
        raise exc.InternalReticulatedError('Should not visit comprehension generators directly')

    def visitName(self, n, varchecks, *args):
        if isinstance(n.ctx, ast.Load) and n.id in varchecks:
            return retic_ast.Check(value=n, type=n.retic_type, lineno=n.lineno, col_offset=n.col_offset)
        else:
            return n
