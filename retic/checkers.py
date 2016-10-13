from . import visitors, consistency

class MethodRecieverChecker(visitors.InPlaceVisitor):
    explore_functions = True
    def visitClassDef(self, n, cls):
        super().dispatch(n, consistency.instance_type(n.retic_type))

    def visitModule(self, n):
        super().dispatch(n, None)

    def visitFunctionDef(self, n, cls):
        pass 
