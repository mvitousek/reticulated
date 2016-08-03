from importlib.abc import Finder, SourceLoader
from os.path import join as _path_join, isdir as _path_isdir, isfile as _path_isfile
from . import exc
import imp, os, sys

import_cache = {}

def _case_ok(directory, check):
    return check in os.listdir(directory if directory else flags.PATH)

def make_importer(typing_context):
    class ReticImporter(Finder, SourceLoader):
        retic = True
        enabled = True

        def __init__(self, path):
            if not self.enabled:
                raise ImportError
            # I think we can raise an ImportError here to bail on this
            # import hook and fallback to the default
            self.path = path

        def find_module(self, fullname, return_path=False):
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
            srcfile = self.get_filename(fullname)
            if srcfile in import_cache:
                return import_cache[srcfile]
                
            from . import imports
            assert srcfile not in imports.import_type_cache
            imports.get_imported_type(srcfile)
            return import_cache[srcfile]

        def load_module(self, fullname):
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

        def exec_module(self, module):
            srcfile = module.__file__
            package = module.__package__
            fullname = module.__name__
            code = self.get_code(module.__name__)
            module.__dict__.update(typing_context)
            module.__file__ = srcfile
            module.__loader__ = self
            module.__package__ = package
            module.__name__ = fullname
            exec(code, module.__dict__)
            return module
    return ReticImporter
