import ast
from vis import Visitor
from typing import *
from relations import *

def typeparse(tyast):
    module = ast.Module(body=[ast.Assign(targets=[ast.Name(id='ty', ctx=ast.Store())], value=tyast)])
    module = ast.fix_missing_locations(module)
    code = compile(module, '<string>', 'exec')
    exec(code)
    return normalize(locals()['ty'])

class Typefinder(Visitor):
    def dispatch_statements(self, n):
        if not hasattr(self, 'visitor'): # preorder may not have been called
            self.visitor = self
        env = {}
        for s in n:
            env.update(self.dispatch(s))
        return env

    def default(self, n):
        return {}

    visitReturn = default

    def visitFunctionDef(self, n):
        argtys = []
        argnames = []
        for arg in n.args.args:
            argnames.append(arg.arg)
            if arg.annotation:
                argtys.append(typeparse(arg.annotation))
            else: argtys.append(Dyn)
        if n.returns:
            ret = typeparse(n.returns)
        else: ret = Dyn
        return {n.name: Function(argtys, ret)}
        
        
