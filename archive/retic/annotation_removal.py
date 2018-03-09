from .copy_visitor import CopyVisitor
import ast
from . import flags

class AnnotationRemovalVisitor(CopyVisitor):
    examine_functions = True
        
    def visitClassDef(self, n, *args):
        bases = self.reduce(n.bases, *args)
        starargs = self.dispatch(n.starargs, *args) if getattr(n, 'starargs', None) else None
        kwargs = self.dispatch(n.kwargs, *args) if getattr(n, 'kwargs', None) else None
        
        declst = []
        for dec in self.reduce(n.decorator_list, *args):
            if isinstance(dec, ast.Call) and \
               isinstance(dec.func, ast.Name) and \
               dec.func.id == 'fields':
                continue
            else: declst.append(dec)

        decorator_list = self.reduce(n.decorator_list, *args)
        body = self.dispatch_statements(n.body, *args)
        keywords = [ast.keyword(k.arg, self.dispatch(k.value, *args)) for k in \
                    getattr(n, 'keywords', [])]
        return ast.ClassDef(name=n.name, bases=bases,
                            keywords=keywords,
                            starargs=starargs, kwargs=kwargs,
                            body=body, decorator_list=declst)

    def visitFunctionDef(self, n, *args):
        fargs = self.dispatch(n.args, *args)
        decorator_list = [self.dispatch(dec, *args) for dec in n.decorator_list]
        if self.examine_functions:
            body = self.dispatch_scope(n.body, *args)
        else: body = n.body
        if flags.PY_VERSION == 3:
            return ast.FunctionDef(name=n.name, args=fargs,
                                   body=body, decorator_list=decorator_list,
                                   returns=self.fix(n.returns), lineno=n.lineno)
        elif flags.PY_VERSION == 2:
            return ast.FunctionDef(name=n.name, args=fargs,
                                   body=body, decorator_list=decorator_list,
                                   lineno=n.lineno)

    def visitarguments(self, n, *args):
        fargs = [self.dispatch(arg, *args) for arg in n.args]
        vararg = self.dispatch(n.vararg, *args) if n.vararg else None 
        defaults = [self.dispatch(default, *args) for default in n.defaults]
        if flags.PY_VERSION == 3:
            kwonlyargs = self.reduce(n.kwonlyargs, *args)
            kw_defaults = [self.dispatch(default, *args) for default in n.kw_defaults]
            
            if flags.PY3_VERSION <= 3:
                varargannotation = self.fix(n.varargannotation) if n.varargannotation else None
                kwargannotation = self.fix(n.kwargannotation) if n.kwargannotation else None
                return ast.arguments(args=fargs, vararg=vararg, varargannotation=varargannotation,
                                     kwonlyargs=kwonlyargs, kwarg=n.kwarg,
                                     kwargannotation=kwargannotation, defaults=defaults, kw_defaults=kw_defaults)
            else:
                return ast.arguments(args=fargs, vararg=vararg,
                                     kwonlyargs=kwonlyargs, kwarg=n.kwarg,
                                     defaults=defaults, kw_defaults=kw_defaults)
        elif flags.PY_VERSION == 2:
            return ast.arguments(args=args, vararg=vararg, kwarg=n.kwarg, defaults=defaults)

    def visitarg(self, n, *args):
        annotation = self.fix(n.annotation) if n.annotation else None
        return ast.arg(arg=n.arg, annotation=annotation)

    def fix(self, n):
        return None
