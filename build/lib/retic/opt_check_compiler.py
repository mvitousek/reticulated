## This module is used to translate from an internal representation of
## transient checks, where they're represented with the
## retic_ast.Check node, into a regular Python representation that can
## be outputted or executed.

from . import copy_visitor, retic_ast, ast_trans, exc
import ast

check_function = '__retic_check__'

class CheckCompiler(copy_visitor.CopyVisitor):
    examine_functions = True

    def reduce(self, ns, *args):
        lst = [self.dispatch(n, *args) for n in ns]
        rlist = []
        for elt in lst:
            if isinstance(elt, retic_ast.ExpandSeq):
                rlist += elt.body
            else:
                rlist.append(elt)
        return rlist

    def dispatch_scope(self, ns, *args):
        lst = [self.dispatch(s, *args) for s in ns]
        rlist = []
        for elt in lst:
            if isinstance(elt, retic_ast.ExpandSeq):
                rlist += elt.body
            else:
                rlist.append(elt)
        return rlist

    def dispatch_statements(self, ns, *args):
        if not hasattr(self, 'visitor'): # preorder may not have been called
            self.visitor = self
        lst = [self.dispatch(s, *args) for s in ns]
        rlist = []
        for elt in lst:
            if isinstance(elt, retic_ast.ExpandSeq):
                rlist += elt.body
            else:
                rlist.append(elt)
        return rlist


    def visitCheck(self, n, *args):
        def get_type(ty):
            if isinstance(ty, retic_ast.OutputAlias) or isinstance(ty, retic_ast.ClassOutputAlias):
                return ty.underlying
            else: return ty

        val = self.dispatch(n.value)
        args = []
        if isinstance(get_type(n.type), retic_ast.Int) or isinstance(get_type(n.type), retic_ast.SingletonInt):
            fn = '__retic_check_int__'
        elif isinstance(get_type(n.type), retic_ast.Float):
            fn = '__retic_check_float__'
        elif isinstance(get_type(n.type), retic_ast.Void):
            fn = '__retic_check_none__'
        elif isinstance(get_type(n.type), retic_ast.Str):
            fn = '__retic_check_str__'
        elif isinstance(get_type(n.type), retic_ast.Bool):
            fn = '__retic_check_bool__'
        elif isinstance(get_type(n.type), retic_ast.Function):
            fn = '__retic_check_callable__'
        elif isinstance(get_type(n.type), retic_ast.Set):
            fn = '__retic_check_set__'
        elif isinstance(get_type(n.type), retic_ast.List):
            fn = '__retic_check_list__'
        elif isinstance(get_type(n.type), retic_ast.Dict):
            fn = '__retic_check_dict__'
        elif isinstance(get_type(n.type), retic_ast.Tuple):
            fn = '__retic_check_tuple__'
            args = [ast.Num(n=len(get_type(n.type).elts), lineno=val.lineno, col_offset=val.col_offset)]
        elif isinstance(get_type(n.type), retic_ast.HTuple):
            fn = '__retic_check_htuple__'
        elif isinstance(get_type(n.type), retic_ast.Dict):
            fn = '__retic_check_dict__'
        elif isinstance(get_type(n.type), retic_ast.Module):
            fn = '__retic_check_module__'
        elif isinstance(get_type(n.type), retic_ast.Instance):
            fn = '__retic_check_instance__'
            args = [n.type.to_ast(lineno=val.lineno, col_offset=val.col_offset)]
        elif isinstance(get_type(n.type), retic_ast.Class):
            fn = '__retic_check_class__'
            args = [n.type.to_ast(lineno=val.lineno, col_offset=val.col_offset).args[0]]
        elif isinstance(get_type(n.type), retic_ast.Union):
            fn = '__retic_check_union__'
            args = [n.type.to_ast(lineno=val.lineno, col_offset=val.col_offset).args[0]]
        elif isinstance(get_type(n.type), retic_ast.Structural):
            fn = '__retic_check_structural__'
            args = [ast.List(elts=[ast.Str(s=k, lineno=val.lineno, col_offset=val.col_offset) for k in get_type(n.type).members], 
                             ctx=ast.Load(), lineno=val.lineno, col_offset=val.col_offset)]
        else: raise exc.InternalReticulatedError(n.type)

        return ast_trans.Call(func=ast.Name(id=fn, ctx=ast.Load(), lineno=n.lineno, col_offset=n.col_offset),
                              args=[val] + args, keywords=[], starargs=None,
                              kwargs=None, lineno=val.lineno, col_offset=val.col_offset)
