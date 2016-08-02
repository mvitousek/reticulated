from . import visitors

class Inferencer(visitors.InPlaceVisitor):
    def visitCall(self, n, *args):
        # do something here
        pass

    def visitFunctionDef(self, n, *args):
        # maybe do something here?
        pass
