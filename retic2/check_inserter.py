from . import copy_visitor, typing, typeparser, retic_ast, ast_trans
import ast

def generateArgumentProtectors(n: ast.arguments, lineno: int, col_offset:int)->typing.List[ast.Expr]:
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
    
        
