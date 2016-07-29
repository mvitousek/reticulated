## The main module for transient check insertion. This relies on
## .retic_type nodes having been inserted by typecheck.py.


from . import copy_visitor, typing, typeparser, retic_ast, ast_trans
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
        return retic_ast.Check(value=ast.Subscript(value=value, slice=slice, ctx=n.ctx),
                               type=n.retic_type, lineno=n.lineno, col_offset=n.col_offset)
        
    def visitFor(self, n, *args):
        # We need to guard the internal body of for loops to make sure that the iteration target has the expected type.

        # Currently this only works for things like 'for x in ...', and will fail for 'for x,y in ...' or 'for a.b in ...'!
        prot = ast.Expr(value=retic_ast.Check(value=ast.Name(id=n.target.id, ctx=ast.Load(),
                                                             lineno=n.lineno, col_offset=n.col_offset),
                                              type=n.target.retic_type, lineno=n.lineno, col_offset=n.col_offset))
        return ast.For(target=self.dispatch(n.target, *args),
                       iter=self.dispatch(n.iter, *args),
                       body=[prot] + self.dispatch_statements(n.body, *args),
                       orelse=self.dispatch_statements(n.orelse, *args),
                       lineno=n.lineno, col_offset=n.col_offset)

    # Missing comprehension stuff. We need to treat it sort of like
    # decompositing assignment, since we can have assignment patterns
    # as targets of comprehensions.
    
        
