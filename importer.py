from visitors import DictGatheringVisitor
import typecheck, os.path, ast, sys, imp, typing, importlib.abc, utils, exc
from os.path import join as _path_join, isdir as _path_isdir, isfile as _path_isfile
from rtypes import *
from typing import Var
from gatherers import WrongContextVisitor
import flags

import_cache = {}
not_found = set()

def _case_ok(directory, check):
    return check in os.listdir(directory if directory else os.getcwd())

def make_importer(typing_context):
    class ReticImporter(importlib.abc.Finder, importlib.abc.SourceLoader):
        def __init__(self, path):
            self.path = path

        def find_module(self, fullname, return_path=False):
            if fullname in flags.IGNORED_MODULES:
                return None
            tail_module = fullname.rpartition('.')[2]
            base_path = _path_join(self.path, tail_module)
            if _path_isdir(base_path) and _case_ok(self.path, tail_module):
                init_filename = '__init__.py'
                full_path = _path_join(base_path, init_filename)
                if (_path_isfile(full_path) and
                    _case_ok(base_path, init_filename)):
                    return full_path if return_path else self
            mod_filename = tail_module + '.py'
            full_path = _path_join(self.path, mod_filename)
            if _path_isfile(full_path) and _case_ok(self.path, mod_filename):
                return full_path if return_path else self
            return None

        def get_filename(self, fullname):
            ret = self.find_module(fullname, return_path=True)
            if ret is not None:
                return ret
            else: raise ImportError

        def get_data(*args):
            raise ImportError

        def module_repr(*args):
            raise ImportError

        def get_code(self, fullname):
            if fullname in import_cache:
                code, _ = import_cache[fullname]
                if code != None:
                    typing.debug('%s found in import cache' % fullname, flags.IMP)
                    return code
            if flags.TIMING:
                flags.pause()
            source_path = self.get_filename(fullname)
            with open(source_path) as srcfile:
                try:
                    typing.debug('Cache miss, compiling %s' % source_path, flags.IMP)
                    py_ast = ast.parse(srcfile.read())
                    checker = typecheck.Typechecker()
                    try:
                        typed_ast, _ = checker.typecheck(py_ast, source_path, 0)
                    except exc.StaticTypeError as e:
                        utils.handle_static_type_error(e)
                    return compile(typed_ast, source_path, 'exec')
                finally: 
                    if flags.TIMING:
                        flags.resume()

        def load_module(self, fullname):
            assert False
            code = self.get_code(fullname)
            ispkg = self.is_package(fullname)
            mod = sys.modules.setdefault(fullname, imp.new_module(fullname))
            srcfile = self.get_filename(fullname)
            mod.__dict__.update(typing_context)
            mod.__file__ = srcfile
            mod.__loader__ = self
            if ispkg:
                mod.__path__ = [srcfile.rsplit(os.path.sep, 1)[0]]
                mod.__package__ = fullname
            else:
                mod.__path__ = [srcfile.rsplit(os.path.sep, 1)[0]]
                mod.__package__ = fullname.rpartition('.')[0]
            mod.__name__ = fullname
            exec(code, mod.__dict__)
            return mod
    return ReticImporter


class ImportFinder(DictGatheringVisitor):
    examine_functions = False

    def typecheck_import(self, module_name, depth):
        if not flags.TYPECHECK_IMPORTS:
            return None
        if module_name in flags.IGNORED_MODULES:
            return None
        if module_name in not_found or module_name in sys.builtin_module_names:
            typing.warn('Imported module %s is a builtin module and cannot be typechecked' % module_name, 1)
            return None
        if module_name in sys.modules:
            typing.warn('Imported module %s is already loaded by Reticulated and cannot be typechecked'\
                            % module_name, 1)
            return None
        for path in sys.path:
            qualname = os.path.join(path, *module_name.split('.')) + '.py'
            if module_name in import_cache:
                _, env = import_cache[module_name]
                return env
            try:
                with open(qualname) as module:
                    typing.debug('Typechecking import ' + qualname, flags.IMP)
                    import_cache[module_name] = None, None
                    assert depth <= flags.IMPORT_DEPTH
                    if depth == flags.IMPORT_DEPTH:
                        typing.warn('Import depth exceeded when typechecking module %s' % qualname, 1)
                        typing.debug('Finished importing ' + qualname, flags.IMP)
                        return None
                    py_ast = ast.parse(module.read())
                checker = typecheck.Typechecker()
                typed_ast, env = checker.typecheck(py_ast, qualname, depth + 1)
                if flags.VERIFY_CONTEXTS:
                    from gatherers import WrongContextVisitor
                    wcv = WrongContextVisitor()
                    wcv.filename = qualname
                    typing.debug('Context checker started for imported module %s' % module_name, flags.PROC)
                    wcv.preorder(typed_ast)
                    typing.debug('Context checker finished for imported module %s' % module_name, flags.PROC)
                import_cache[module_name] = compile(typed_ast, module_name, 'exec'), env
                typing.debug('Finished importing ' + qualname, flags.IMP)
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
            if impenv is None:
                env[Var(name)] = Dyn
            else: 
                env[Var(name)] = Object('', {k.var: impenv[k] for k in impenv if isinstance(k, Var)})
        return env

    def visitImportFrom(self, n, depth):
        if n.level is not None and n.level != 0:
            impenv = None
        else: impenv = self.typecheck_import(n.module, depth)
        wasemp = False
        if impenv is None:
            impenv = {}
            wasemp = True
        env = {}
        for alias in n.names:
            member = alias.name
            if member == '*':
                if wasemp:
                    typing.warn('Unable to import type definitions from %s due to *-import' % n.module, 0)
                return impenv
            name = alias.asname if alias.asname else alias.name
            if Var(member) in impenv:
                env[Var(name)] = impenv[Var(member)]
            else: env[Var(name)] = Dyn
            if TypeVariable(member) in impenv:
                env[TypeVariable(name)] = impenv[TypeVariable(member)]
        return env

