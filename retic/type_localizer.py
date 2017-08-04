from . import visitors, retic_ast, exc

def invert(env):
    ret = {}
    for k in env:
        if isinstance(env[k], dict):
            local = invert(env[k])
            ret.update({ty: k + '.' + local[ty] for ty in local})
        elif isinstance(env[k], retic_ast.Instance):
            ret[env[k].instanceof] = k
        
    return ret

class TypeLocalityFinder(visitors.DictGatheringVisitor):
    def visitClassDef(self, n, *args):
        ret = super().visitClassDef(n, *args)
        ret = {k: n.name + '.' + ret[k] for k in ret}
        ret.update(invert(n.retic_import_aliases))
        ret[n.retic_type.type] = n.name
        return ret

    def visitModule(self, n, *args):
        ret = super().visitModule(n, *args)
        ret.update(invert(n.retic_import_aliases))
        return ret

class TypeLocalizer(visitors.InPlaceVisitor):
    examine_functions = True

    def visitModule(self, n):
        env = TypeLocalityFinder().preorder(n)
        super().visitModule(n, env)

    def visitClassDef(self, n, env):
        locals = TypeLocalityFinder().preorder(n)
        env = env.copy()
        env.update(locals)
        super().visitClassDef(n, env)

    def visitCheck(self, n, env):
        super().visitCheck(n, env)
        if isinstance(n.type, retic_ast.Instance) and n.type.instanceof in env:
            n.type = retic_ast.OutputAlias(env[n.type.instanceof], n.type)
        elif isinstance(n.type, retic_ast.Class) and n.type in env:
            n.type = retic_ast.ClassOutputAlias(env[n.type], n.type)
