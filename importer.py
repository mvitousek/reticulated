from visitors import DictGatheringVisitor
import typecheck, os.path, ast, sys, imp, typing
from rtypes import *
from typing import Var
import flags

import_cache = {}
not_found = set()

def make_importer(typing_context):
    class ReticImporter:
        def __init__(self, path):
            quit()
            self.path = path   
     
        def find_module(self, fullname):
            qualname = os.path.join(self.path, *fullname.split('.')) + '.py'
            try: 
                with open(qualname):
                    return self
            except IOError:
                return None

        def get_code(self, fileloc, filename):
            typing.debug('Importing %s' % fileloc, flags.IMP)
            if fileloc in import_cache:
                code, _ = import_cache[fileloc]
                if code != None:
                    typing.debug('%s found in import cache' % fileloc, flags.IMP)
                    return code
            with open(fileloc) as srcfile:
                typing.debug('Cache miss, compiling %s' % fileloc, flags.IMP)
                py_ast = ast.parse(srcfile.read())
                checker = typecheck.Typechecker()
                typed_ast, _ = checker.typecheck(py_ast, fileloc, 0)
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


class ImportFinder(DictGatheringVisitor):
    examine_functions = False

    def typecheck_import(self, module_name, depth):
        if module_name in not_found or module_name in sys.builtin_module_names:
            return None
        if module_name in sys.modules:
            typing.warn('Imported module %s is already loaded by Reticulated and cannot be typechecked'\
                            % module_name, 1)
            return None
        for path in sys.path:
            qualname = os.path.join(path, *module_name.split('.')) + '.py'
            if qualname in import_cache:
                _, env = import_cache[qualname]
                return env
            try:
                with open(qualname) as module:
                    typing.debug('Typechecking import ' + qualname, flags.IMP)
                    import_cache[qualname] = None, None
                    assert depth <= flags.IMPORT_DEPTH
                    if depth == flags.IMPORT_DEPTH:
                        typing.warn('Import depth exceeded when typechecking module %s' % qualname, 1)
                        return None
                    py_ast = ast.parse(module.read())
                checker = typecheck.Typechecker()
                typed_ast, env = checker.typecheck(py_ast, qualname, depth + 1)
                import_cache[qualname] = compile(typed_ast, module_name, 'exec'), env
                return env
            except IOError:
                continue
        not_found.add(module_name)
        return None
    
    def visitImport(self, n, depth):
        env = {}
        for alias in n.names:
            module = alias.name
            name = alias.asname if alias.asname else alias.name
            impenv = self.typecheck_import(module, depth)
            if impenv == None:
                env[Var(name)] = Dyn
            else: env[Var(name)] = Object('', {k.var: impenv[k] for k in impenv if isinstance(k, Var)})
        return env

    def visitImportFrom(self, n, depth):
        impenv = self.typecheck_import(n.module, depth)
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

