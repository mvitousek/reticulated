from . import visitors, consistency, retic_ast, exc

class ReturnChecker(visitors.BooleanOrVisitor):
    ## This visitor looks at function return values and reports an error if either
    ## - A function can return a value that doesn't correspond to the
    ##   function's annotated return type
    ## - Not all paths through a function lead to either an exception
    ##   being raised or a value being returned.

    def visitModule(self, n):
        return self.dispatch_statements(n.body, None)
    
    def visitFunctionDef(self, n, retty, *args):        
        body = self.dispatch_statements(n.body, n.retic_return_type, *args)
        if not body and not consistency.assignable(n.retic_return_type, retic_ast.Void()):
            raise exc.StaticTypeError(n, 'A value is not necessarily returned from this function')

        return False

    def visitClassDef(self, n, retty, *args):
        body = self.dispatch_statements(n.body, None, *args)
        return False

    def visitReturn(self, n, retty, *args):
        if n.value:
            ty = n.value.retic_type
        else: 
            ty = retic_ast.Void()

        if consistency.assignable(retty, ty):
            return True
        else:
            targ = n.value if n.value else n
            raise exc.StaticTypeError(targ, 'Returned value has type {}, but function is annotated to return values of type {}'.format(ty, retty))

    def visitRaise(self, n, retty, *args):
        return True

    def visitClass(self, n, retty, *args):
        return False

    # Control flow stuff
    def visitIf(self, n, *args):
        body = self.dispatch_statements(n.body, *args)
        orelse = self.dispatch_statements(n.orelse, *args) if n.orelse else self.empty_stmt()
        return body and orelse

    def visitFor(self, n, *args):
        body = self.dispatch_statements(n.body, *args)
        orelse = self.dispatch_statements(n.orelse, *args) if n.orelse else self.empty_stmt()
        return body and orelse
        
    def visitWhile(self, n, *args):
        body = self.dispatch_statements(n.body, *args)
        orelse = self.dispatch_statements(n.orelse, *args) if n.orelse else self.empty_stmt()
        return body and orelse

    def visitWith(self, n, *args):
        return self.dispatch_statements(n.body, *args)

    
    # Python 2.7, 3.2
    def visitTryExcept(self, n, *args):
        body = self.dispatch_statements(n.body, *args)
        handlers = self.reduce_stmt(n.handlers, *args)
        orelse = self.dispatch_statements(n.orelse, *args) if n.orelse else self.empty_stmt()
        return (body and handlers) or (orelse and handlers)

    # Python 2.7, 3.2
    def visitTryFinally(self, n, *args):
        body = self.dispatch_statements(n.body, *args)
        finalbody = self.dispatch_statements(n.finalbody, *args)
        return body or finalbody
    
    # Python 3.3
    def visitTry(self, n, *args):
        body = self.dispatch_statements(n.body, *args)
        handlers = self.reduce_stmt(n.handlers, *args)
        orelse = self.dispatch_statements(n.orelse, *args) if n.orelse else self.empty_stmt()
        finalbody = self.dispatch_statements(n.finalbody, *args)
        return (body and handlers) or (orelse and handlers) or finalbody

    def visitExceptHandler(self, n, *args):
        return self.dispatch_statements(n.body, *args)
