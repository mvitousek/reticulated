from .. import copy_visitor, retic_ast
from . import ctypes, constraints

import ast

def subst(cty, sol):
    for const in sol:
        if isinstance(const, constraints.DefC):
            cty = cty.subst(const.l, const.r)
    return cty

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

    def visitModule(self, n, sol, *args):
        body = self.dispatch_scope(n.body, sol, n.retic_cctbl, *args)
        return ast.Module(body=body)


    def visitcheck_generic(self, cx, n, sol, ctbl, *args):
        val = self.dispatch(n.value, sol, ctbl, *args)
        
        if isinstance(n.type, retic_ast.Dyn):
            return val
        elif isinstance(n.type, retic_ast.Void):
            return val
        elif isinstance(n.type, retic_ast.Primitive) and (isinstance(val, ast.Num) or isinstance(val, ast.Str)):
            return val
        elif isinstance(n.type, retic_ast.List) and (isinstance(val, ast.List) or isinstance(val, ast.ListComp)):
            return val
        elif isinstance(n.type, retic_ast.HTuple) and isinstance(val, ast.Tuple):
            return val
        elif isinstance(n.type, retic_ast.Tuple) and (isinstance(val, ast.Tuple) and len(val.elts) == len(n.type.elts)):
            return val
        elif isinstance(n.type, retic_ast.Set) and (isinstance(val, ast.Set) or isinstance(val, ast.SetComp)):
            return val
        elif isinstance(n.type, retic_ast.Dict) and (isinstance(val, ast.Dict) or isinstance(val, ast.DictComp)):
            return val
        
        rty = n.type
        cty = subst(n.value.retic_ctype, sol)
        matchcode = ctypes.match(cty, rty, ctbl)
        if matchcode == ctypes.CONFIRM:
            return val
        elif matchcode == ctypes.UNCONFIRM:
            print('#Keeping check at line {} ({} ~ {})'.format(n.lineno, cty, rty))
            ret = cx(value=val, type=n.type, lineno=n.lineno, col_offset=n.col_offset)
            return ret
        elif matchcode == ctypes.DENY:
            print('#Detected check that will always fail at line {} ({} =/= {})'.format(n.lineno, cty, rty))
            ret = cx(value=val, type=n.type, lineno=n.lineno, col_offset=n.col_offset)
            return ret
        elif matchcode == ctypes.PENDING:
            print('#Falling back at line {} ({} unsolved)'.format(n.lineno, cty))
            ret = cx(value=val, type=n.type, lineno=n.lineno, col_offset=n.col_offset)
            return ret
        else: raise Exception()
        
    
    def visitProtCheck(self, n, *args):
        return self.visitcheck_generic(retic_ast.ProtCheck, n, *args)

    def visitUseCheck(self, n, *args):
        return self.visitcheck_generic(retic_ast.UseCheck, n, *args)

    def visitCheck(self, n, *args):
        return self.visitcheck_generic(retic_ast.Check, n, *args)


    def visitExpr(self, n, *args):
        val = self.dispatch(n.value, *args)
        if (isinstance(n.value, retic_ast.Check) or isinstance(n.value, retic_ast.ProtCheck) or isinstance(n.value, retic_ast.UseCheck)) and isinstance(val, ast.Name):
            return Tombstone()
        else:
            return ast.Expr(value=val, lineno=n.lineno)
            
    def visitAssign(self, n, *args):
        value = self.dispatch(n.value, *args)
        targets = self.reduce(n.targets, *args)
        if not isinstance(value, retic_ast.Check) or not isinstance(value.value, ast.Name):
            return ast.Assign(targets=targets, value=value, lineno=n.lineno, col_offset=n.col_offset)
        for target in targets:
            if isinstance(n, ast.List) or isinstance(n, ast.Tuple) or isinstance(n, ast.Starred):
                # These we actually can optimize further (maybe not
                # starred?), if we know that all subassignees are not
                # names with differing types from the value.
                return ast.Assign(targets=targets, value=value, lineno=n.lineno, col_offset=n.col_offset)
            if isinstance(target, ast.Name) and target.retic_type != value.value.retic_type:
                return ast.Assign(targets=targets, value=value, lineno=n.lineno, col_offset=n.col_offset)
        return ast.Assign(targets=targets, value=value.value, lineno=n.lineno, col_offset=n.col_offset)
        
        
