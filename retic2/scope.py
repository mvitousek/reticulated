from . import visitors, retic_ast, typing, typeparser, exc
import ast

tydict = typing.Alias(typing.Dict[str, retic_ast.Type])

def getFunctionScope(n: ast.FunctionDef, surrounding: tydict)->tydict:
    local = InitialScopeFinder().preorder(n.body)
    args = getLocalArgTypes(n.args)
    scope = surrounding.copy()
    scope.update(args)
    scope.update(local)
    return scope

def getLambdaScope(n: ast.Lambda, surrounding: tydict)->tydict:
    args = getLocalArgTypes(n.args)
    scope = surrounding.copy()
    scope.update(args)
    return scope


def getModuleScope(n: ast.Module)->tydict:
    return InitialScopeFinder().preorder(n.body)

def getLocalArgTypes(n: ast.arguments)->tydict:
    args = {}
    for arg in n.args:
        ty = typeparser.typeparse(arg.annotation)
        args[arg.arg] = arg.retic_type = ty
    for arg in n.kwonlyargs:
        ty = typeparser.typeparse(arg.annotation)
        args[arg.arg] = arg.retic_type = ty
    if n.vararg:
        ty = typeparser.typeparse(n.vararg.annotation)
        args[n.vararg.arg]  = n.vararg.retic_type = ty
    if n.kwarg:
        ty = typeparser.typeparse(n.kwarg.annotation)
        args[n.kwarg.arg]  = n.kwarg.retic_type = ty
    return args
    

class InitialScopeFinder(visitors.DictGatheringVisitor):
    examine_functions = False

    def combine_stmt(self, s1: tydict, s2: tydict)->tydict:
        for k in s1:
            if k in s2 and s1[k] != s2[k]:
                raise exc.IncompatibleBindingsError()
        s1.update(s2)
        return s1
    
    def visitFunctionDef(self, n: ast.FunctionDef)->tydict:
        argtys = []
        for arg in n.args.args:
            if arg.annotation:
                argty = typeparser.typeparse(arg.annotation)
            else:
                argty = retic_ast.Dyn()
            argtys.append(argty)
        retty = typeparser.typeparse(n.returns)
        return {n.name: retic_ast.Function(retic_ast.PosAT(argtys), retty)}

    def visitAssign(self, n: ast.Assign)->tydict:
        asgn_scope = {}
        for targ in n.targets:
            if isinstance(targ, ast.Name):
                asgn_scope[targ.id] = retic_ast.Dyn()
        return asgn_scope
        
