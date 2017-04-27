from .. import visitors, retic_ast
from . import variables
import ast


class VariableRemover(visitors.InPlaceVisitor):
    examine_functions = True
    
    def dispatch(self, n, solution, *args):
        super().dispatch(n, solution, *args)
        if hasattr(n, 'retic_check_type'):
            if isinstance(n.retic_check_type, retic_ast.FlowVariable):
                if n.retic_check_type.var in solution:
                    print("{} =>{} {}".format(n.retic_check_type.type, n.retic_check_type.var, solution[n.retic_check_type.var]))
                    n.retic_check_type = solution[n.retic_check_type.var]
                else:
                    print(n.retic_check_type.var, 'not in', solution)
                    n.retic_check_type = n.retic_check_type.type
