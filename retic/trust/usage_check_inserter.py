## The main module for transient check insertion. This relies on
## .retic_type nodes having been inserted by typecheck.py.


from .. import copy_visitor, typing, typeparser, retic_ast, ast_trans, flags, exc, scope
import ast


class UsageCheckInserter(copy_visitor.CopyVisitor):
    examine_functions = True
    def visitModule(self, n):
        return ast.Module(body=self.dispatch(n.body, set()))
    
    def visitCall(self, n, *args):
        call =  ast_trans.Call(func=self.dispatch(n.func, *args),
                               args=self.reduce(n.args, *args),
                               keywords=[ast.keyword(arg=k.arg, value=self.dispatch(k.value, *args))\
                                         for k in n.keywords],
                               starargs=self.dispatch(n.starargs, *args) if getattr(n, 'starargs', None) else None,
                               kwargs=self.dispatch(n.kwargs, *args) if getattr(n, 'kwargs', None) else None,
                               lineno=n.lineno, col_offset=n.col_offset)
        call.func = retic_ast.UseCheck(value=call.func, type=retic_ast.Function(retic_ast.PosAT([retic_ast.Dyn()] * len(n.args)), retic_ast.Dyn()),
                                    lineno=n.lineno, col_offset=n.col_offset)
        return call
        
    def visitAttribute(self, n, *args):
        attr = ast.Attribute(value=self.dispatch(n.value, *args),
                             attr=n.attr, ctx=n.ctx,
                             lineno=n.lineno, col_offset=n.col_offset)
        if isinstance(n.ctx, ast.Load):
            attr.value = retic_ast.UseCheck(value=attr.value, type=retic_ast.Structural({attr.attr:retic_ast.Dyn()}), lineno=n.lineno, col_offset=n.col_offset)
        return attr

    def visitSubscript(self, n, *args):
        value = self.dispatch(n.value, *args)
        slice = self.dispatch(n.slice, *args)
        sub = ast.Subscript(value=value, slice=slice, ctx=n.ctx, lineno=n.lineno, col_offset=n.col_offset)
        if isinstance(n.ctx, ast.Load):
            sub.value = retic_ast.UseCheck(value=sub.value, type=retic_ast.Subscriptable(), lineno=n.lineno, col_offset=n.col_offset)
        return sub


    def visitFor(self, n, *args):
        # Check that the iteration target is iterable
        return super().visitFor(n, *args)

    def visitAssign(self, n, *args):
        # Check that complex targets support things maybe?
        return super().visitAssign(n, *args)
        
    def handleComprehensions(self, comps, lineno, offset, *args):
        ccomps = []
    
        for c in comps:
            ccomps.append(ast.comprehension(target=self.dispatch(c.target, *args),
                                            iter=retic_ast.UseCheck(value=self.dispatch(c.iter), type=retic_ast.Subscriptable(), lineno=lineno, col_offset=offset),
                                            ifs=self.reduce(c.ifs, *args)))
        return ccomps, []
        
    def visitListComp(self, n, varchecks, *args):
        # In comprehensions, we can't generate protectors to guard
        # arguments since the body is just an expression. Instead we
        # add variables to varchecks to indicate in visitName that the
        # variable should be checked directly. This can lead to
        # duplicated checks but I suspect that's relatively rare.
        
        generators, varchecks = self.handleComprehensions(n.generators, n.lineno, n.col_offset, varchecks, *args)
        
        elt = self.dispatch(n.elt, varchecks, *args)
        return ast.ListComp(elt=elt, generators=generators)

    def visitSetComp(self, n, varchecks, *args):
        
        generators, varchecks = self.handleComprehensions(n.generators, n.lineno, n.col_offset,varchecks, *args)
            
        elt = self.dispatch(n.elt, varchecks, *args)
        return ast.SetComp(elt=elt, generators=generators)

    def visitDictComp(self, n, varchecks, *args):
        
        generators, varchecks = self.handleComprehensions(n.generators, n.lineno, n.col_offset,varchecks, *args)
            
        key = self.dispatch(n.key, varchecks, *args)
        value = self.dispatch(n.value, varchecks, *args)
        return ast.DictComp(key=key, value=value, generators=generators)

    def visitGeneratorExp(self, n, varchecks, *args):
        
        generators, varchecks = self.handleComprehensions(n.generators, n.lineno, n.col_offset,varchecks, *args)
            
        elt = self.dispatch(n.elt, varchecks, *args)
        return ast.GeneratorExp(elt=elt, generators=generators)

