from . import copy_visitor, retic_ast
import ast

class Tombstone(ast.stmt): pass

class CheckRemover(copy_visitor.CopyVisitor):
    # Removes unneeded checks, like checks where the type of the check
    # is Dyn.  In the case of argument protectors (the checks inserted
    # at the entry to functions), when we remove them we might leave
    # behind a "useless" expression, one which didn't appear in the
    # original program but doesn't have any typechecking value. We
    # detect these cases by looking at Expr statements (the kind of
    # statement representing an expression alone on a line). If the
    # value of the Expr (i.e. the expression contained within it) was
    # a retic_ast.Check before the recursive call, but just an
    # ast.Name afterwards, we replace the Expr with a special
    # Tombstone value. Then, when function bodies are being
    # reconstructed to be outputted (using the reduce, dispatch_scope,
    # and dispatch_statements methods), we look for Tombstone values
    # and filter them out. Tombstones should NEVER exist in the final
    # outputted AST.

    examine_functions = True
    
    def reduce(self, ns, *args):
        lst = [self.dispatch(n, *args) for n in ns]
        return [l for l in lst if not isinstance(l, Tombstone)]

    def dispatch_scope(self, ns, *args):
        lst = [self.dispatch(s, *args) for s in ns]
        return [l for l in lst if not isinstance(l, Tombstone)]

    def dispatch_statements(self, ns, *args):
        if not hasattr(self, 'visitor'): # preorder may not have been called
            self.visitor = self
        lst = [self.dispatch(s, *args) for s in ns]
        return [l for l in lst if not isinstance(l, Tombstone)]

    def visitCheck(self, n, *args):
        val = self.dispatch(n.value)

        def untrust(ty):
            if isinstance(ty, retic_ast.Trusted):
                return ty.type
            else: return ty

            
        if isinstance(getattr(n.value, 'retic_check_type', None), retic_ast.Trusted):
            return val

        if isinstance(n.type, retic_ast.Dyn):
            return val
        if isinstance(n.type, retic_ast.Void):
            return val
        elif isinstance(n.type, retic_ast.Primitive) and (isinstance(n.value, ast.Num) or isinstance(n.value, ast.Str)):
            return val
        elif isinstance(n.type, retic_ast.List) and (isinstance(n.value, ast.List) or isinstance(n.value, ast.ListComp)):
            return val
        elif isinstance(n.type, retic_ast.HTuple) and isinstance(n.value, ast.Tuple):
            return val
        elif isinstance(n.type, retic_ast.Tuple) and (isinstance(n.value, ast.Tuple) and len(n.value.elts) == len(n.type.elts)):
            return val
        elif isinstance(n.type, retic_ast.Set) and (isinstance(n.value, ast.Set) or isinstance(n.value, ast.SetComp)):
            return val
        elif isinstance(n.type, retic_ast.Dict) and (isinstance(n.value, ast.Dict) or isinstance(n.value, ast.DictComp)):
            return val
        else:
            return retic_ast.Check(value=val, type=n.type, lineno=n.lineno, col_offset=n.col_offset)

    def visitExpr(self, n, *args):
        val = self.dispatch(n.value)
        if isinstance(n.value, retic_ast.Check) and isinstance(val, ast.Name):
            return Tombstone()
        else:
            return ast.Expr(value=val, lineno=n.lineno)
            
    def visitAssign(self, n, *args):
        value = self.dispatch(n.value)
        if not isinstance(value, retic_ast.Check) or not isinstance(value.value, ast.Name):
            return ast.Assign(targets=n.targets, value=value, lineno=n.lineno, col_offset=n.col_offset)
        for target in n.targets:
            if isinstance(n, ast.List) or isinstance(n, ast.Tuple) or isinstance(n, ast.Starred):
                # These we actually can optimize further (maybe not
                # starred?), if we know that all subassignees are not
                # names with differing types from the value.
                return ast.Assign(targets=n.targets, value=value, lineno=n.lineno, col_offset=n.col_offset)
            if isinstance(target, ast.Name) and target.retic_type != value.value.retic_type:
                return ast.Assign(targets=n.targets, value=value, lineno=n.lineno, col_offset=n.col_offset)
        return ast.Assign(targets=n.targets, value=value.value, lineno=n.lineno, col_offset=n.col_offset)
        
        
