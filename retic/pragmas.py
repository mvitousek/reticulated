from . import visitors, typeparser, ast_trans
import ast

class ClassAnnotationHandler(visitors.InPlaceVisitor):
    def visitClassDef(self, n, aliases, *args):
        if not hasattr(n, 'retic_annot_fields'):
            n.retic_annot_fields = {}
        if not hasattr(n, 'retic_annot_members'):
            n.retic_annot_members = {}
        for dec in n.decorator_list:
            if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Name) and \
               dec.func.id == 'fields':
                if len(dec.args) != 1 or dec.keywords or ast_trans.starargs(dec) or ast_trans.kwargs(dec):
                    raise exc.MalformedTypeError(dec, '"fields" annotation expects exactly one argument')
                elif not isinstance(dec.args[0], ast.Dict):
                    raise exc.MalformedTypeError(dec.args[0], '"fields" annotation expects a dictionary')
                elif not all(isinstance(k, ast.Str) for k in dec.args[0].keys):
                    raise exc.MalformedTypeError(dec.args[0], '"fields" annotation expects a dictionary mapping attribute names as strings to types')
                else:
                    n.retic_annot_fields.update({k.s: typeparser.typeparse(v, aliases) for k, v in zip(dec.args[0].keys, dec.args[0].values)})
            elif isinstance(dec, ast.Call) and isinstance(dec.func, ast.Name) and \
               dec.func.id == 'members':
                if len(dec.args) != 1 or dec.keywords or ast_trans.starargs(dec) or ast_trans.kwargs(dec):
                    raise exc.MalformedTypeError(dec, '"members" annotation expects exactly one argument')
                elif not isinstance(dec.args[0], ast.Dict):
                    raise exc.MalformedTypeError(dec.args[0], '"members" annotation expects a dictionary')
                elif not all(isinstance(k, ast.Str) for k in dec.args[0].keys):
                    raise exc.MalformedTypeError(dec.args[0], '"members" annotation expects a dictionary mapping attribute names as strings to types')
                else:
                    n.retic_annot_members.update({k.s: typeparser.typeparse(v, aliases) for k, v in zip(dec.args[0].keys, dec.args[0].values)})
        self.dispatch(n.body, aliases, *args)
