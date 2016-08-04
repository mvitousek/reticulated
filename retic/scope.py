from . import visitors, retic_ast, typing, typeparser, exc, consistency
import ast

## This module figures out the environment for a given scope. 

tydict = typing.Dict[str, retic_ast.Type]

class InconsistentAssignment(Exception): pass

def gather_aliases(n, env):
    aliases = {}
    while True:
        last_aliases = aliases
        lenv = env.copy()
        lenv.update(last_aliases)
        aliases = TypeAliasFinder().preorder(n.body, lenv)
        if aliases == last_aliases:
            break
    renv = env.copy()
    renv.update(aliases)
    return renv

class TypeAliasFinder(visitors.DictGatheringVisitor):
    def combine_stmt(self, s1: tydict, s2: tydict)->tydict:
        for k in s1:
            if k in s2 and s1[k] != s2[k]:
                del s1[k], s2[k]
        s1.update(s2)
        return s1

    def visitAssign(self, n, env, *args):
        try:
            ret = {}
            parsed = typeparser.typeparse(n.value, env)
        except exc.MalformedTypeError:
            return {}

        for target in n.targets:
            if isinstance(target, ast.Name):
                if target.id in typeparser.type_names:
                    raise exc.StaticTypeError(n.value, 'Cannot redefine basic types like {}'.format(target.id))
                ret[target.id] = parsed

        return ret

class InitialScopeFinder(visitors.DictGatheringVisitor):
    examine_functions = False

    def combine_stmt(self, s1: tydict, s2: tydict)->tydict:
        for k in s1:
            if k in s2 and s1[k] != s2[k]:
                raise InconsistentAssignment(k, s1[k], s2[k])
        s1.update(s2)
        return s1
    
    def visitClassDef(self, n, *args):
        return {}

    def visitFunctionDef(self, n: ast.FunctionDef, env, *args)->tydict:
        argbindings = []
        for arg in n.args.args:
            if arg.annotation:
                argty = typeparser.typeparse(arg.annotation, env)
            else:
                argty = retic_ast.Dyn()
            argbindings.append((arg.arg, argty))

        if n.args.vararg or n.args.kwonlyargs or n.args.kwarg or n.args.defaults:
            argsty = retic_ast.ApproxNamedAT(argbindings)
        else:
            argsty = retic_ast.NamedAT(argbindings)

        retty = typeparser.typeparse(n.returns, env)

        funty = retic_ast.Function(argsty, retty)
        n.retic_type = funty

        return {n.name: funty}

        
class WriteTargetFinder(visitors.SetGatheringVisitor):
    examine_functions = False
    
    def visitcomprehension(self, n, *args):
        return set()

    def visitName(self, n: ast.Name)->typing.Set[str]:
        if isinstance(n.ctx, ast.Store):
            return { n.id }
        else: return set()


    def visitWith(self, n):
        raise exc.UnimplementedExcpetion('with')

class AssignmentFinder(visitors.SetGatheringVisitor):
    examine_functions = False
    
    def visitAssign(self, n: ast.Assign):
        return { (targ, n.value, 'ASSIGN') for targ in n.targets if not isinstance(targ, ast.Subscript) and not isinstance(targ, ast.Attribute) }

    def visitAugAssign(self, n: ast.AugAssign):
        if not isinstance(n.target, ast.Subscript) and not isinstance(n.target, ast.Attribute):
            return { (n.target, n.value, 'ASSIGN') }
        else: return set()

    def visitFor(self, n: ast.For): 
        if not isinstance(n.target, ast.Subscript) and not isinstance(n.target, ast.Attribute):
            return set.union({ (n.target, n.iter, 'FOR') }, self.dispatch(n.body), self.dispatch(n.orelse))
        else: return set.union(self.dispatch(n.body), self.dispatch(n.orelse))

    def visitWith(self, n):
        raise exc.UnimplementedExcpetion('with')
        
