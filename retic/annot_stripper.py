from . import copy_visitor, ast_trans
import ast

class AnnotationStripper(copy_visitor.CopyVisitor):
    examine_functions = True
    examine_classes = True
    def visitarg(self, n):
        return ast.arg(n.arg, None)

    def visitClassDef(self, n, *args):
        bases = self.reduce(n.bases, *args)
        starargs = self.dispatch(n.starargs, *args) if getattr(n, 'starargs', None) else None
        kwargs = self.dispatch(n.kwargs, *args) if getattr(n, 'kwargs', None) else None
        decorator_list = self.reduce(n.decorator_list, *args)
        decorator_list = [dec for dec in decorator_list if not (isinstance(dec, ast.Call) and isinstance(dec.func, ast.Name) and dec.func.id in ['fields', 'members'])]
        body = self.dispatch_statements(n.body, *args)
        keywords = [ast.keyword(k.arg, self.dispatch(k.value, *args)) for k in \
                    getattr(n, 'keywords', [])]
        return ast_trans.ClassDef(name=n.name, 
                                  bases=bases,
                                  keywords=keywords,
                                  starargs=starargs,
                                  kwargs=kwargs,
                                  body=body,
                                  decorator_list=decorator_list)

    def visitFunctionDef(self, n, *args):
        ret = super().visitFunctionDef(n, *args)
        ret.returns = None
        return ret
