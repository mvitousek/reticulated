from visitors import DictGatheringVisitor
import typecheck, os.path, ast, sys
from rtypes import *
from typing import Var

import_cache = {}

def make_importer(typing_context):
    class ReticImporter:
        def __init__(self, path):
            self.path = path   
     
        def find_module(self, fullname):
            qualname = os.path.join(self.path, *fullname.split('.')) + '.py'
            try: 
                with open(qualname):
                    return self
            except IOError:
                return None

        def get_code(self, fileloc, filename):
            if fileloc in import_cache:
                code, _ = import_cache[fileloc]
                return code
            with open(fileloc) as srcfile:
                py_ast = ast.parse(srcfile.read())
                checker = typecheck.Typechecker()
                typed_ast, _ = checker.typecheck(py_ast)
                return compile(typed_ast, filename, 'exec')

        def is_package(self, fileloc):
            return os.path.isdir(fileloc) and glob.glob(os.path.join(fileloc, '__init__.py*'))

        def load_module(self, fullname):    
            qualname = os.path.join(self.path, *fullname.split('.')) + '.py'
            code = self.get_code(qualname, fullname)
            ispkg = self.is_package(fullname)
            mod = sys.modules.setdefault(fullname, imp.new_module(fullname))
            mod.__file__ = qualname
            mod.__loader__ = self
            if ispkg:
                mod.__path__ = []
                mod.__package__ = fullname
            else:
                mod.__package__ = fullname.rpartition('.')[0]
            mod.__dict__.update(typing_context)
            exec(code, mod.__dict__)
            return mod
    return ReticImporter

checked = set()

class ImportFinder(DictGatheringVisitor):
    examine_functions = False

    def typecheck_import(self, module_name):
        for path in sys.path:
            qualname = os.path.join(path, *module_name.split('.')) + '.py'
            if qualname in import_cache:
                print('Cache hit', qualname)
                _, env = import_cache[qualname]
                return env
            try:
                with open(qualname) as module:
                    print('Lookup hit', qualname)
                    import_cache[qualname] = None, None
                    py_ast = ast.parse(module.read())
                    checker = typecheck.Typechecker()
                    typed_ast, env = checker.typecheck(py_ast)
                    import_cache[qualname] = compile(typed_ast, module_name, 'exec'), env
                    print('Finish Lookup', qualname)
                    return env
            except IOError:
                continue
        print(module_name, 'not found')
        checked.add(module_name)
        return None
    
    def visitImport(self, n):
        print(ast.dump(n))
        env = {}
        for alias in n.names:
            module = alias.name
            name = alias.asname if alias.asname else alias.name
            impenv = self.typecheck_import(module)
            if impenv == None:
                env[Var(name)] = Dyn
            else: env[Var(name)] = Object('', {k.var: impenv[k] for k in impenv if isinstance(k, Var)})
        return env

    def visitImportFrom(self, n):
        impenv = self.typecheck_import(n.module)
        if impenv == None:
            impenv = {}
        env = {}
        for alias in n.names:
            member = alias.name
            if member == '*':
                return impenv
            name = alias.asname if alias.asname else alias.name
            if Var(name) in impenv:
                env[Var(name)] = impenv[Var(name)]
            else: env[Var(name)] = Dyn
        return env

