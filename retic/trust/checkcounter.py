from .. import visitors

class CheckCounter(visitors.CountingVisitor):
    examine_functions = True
    def visitCheck(self, n, *args):
        ct = super().visitCheck(n, *args)
        return ct + 1
    def visitProtCheck(self, n, *args):
        ct = super().visitProtCheck(n, *args)
        return ct + 1
