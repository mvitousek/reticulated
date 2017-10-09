from . import copy_visitor, ast_trans
import ast

class AnnotationStripper(copy_visitor.CopyVisitor):
    examine_functions = True

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
        ret.decorator_list = [dec for dec in ret.decorator_list if not (isinstance(dec, ast.Name) and dec.id in ['positional'])]
        ret.returns = None
        return ret

def main():
    import argparse, sys, os
    from . import static
    parser = argparse.ArgumentParser(description='Strip type annotations')
    parser.add_argument('program', help='a Python program to have annotations stripped (.py extension required)', default=None)
    parser.add_argument('target', help='a filename that the result will be written to', default=None)

    args = parser.parse_args(sys.argv[1:])
    try:
        with open(args.program, 'r') as program:
            sys.path.insert(1, os.path.sep.join(os.path.abspath(args.program).split(os.path.sep)[:-1]))

            st, srcdata = static.parse_module(program)
            st = AnnotationStripper().preorder(st)
            with open(args.target, 'w', encoding='utf-8') as write:
                static.emit_module(st, file=write, imports=False)
    except IOError as e:
        print(e)

if __name__ == '__main__':
    main()

