from . import visitors, exc, typing, retic_ast, importhook
import os.path, sys, ast

import_type_cache = {}

def get_imported_type(file):
    from . import static
    if file is None:
        return retic_ast.Dyn()
    elif file in import_type_cache:
        return import_type_cache[file]
    else:
        with open(file, 'r') as data:
            st, srcdata = static.parse_module(data)
        
        # Put a placeholder type here to prevent divergence
        import_type_cache[file] = retic_ast.Module({})
        st = static.typecheck_module(st, srcdata)
        import_type_cache[file] = st.retic_type
        compile_file(st, srcdata, file)
        return st.retic_type
            
def compile_file(st, srcdata, file):
    from . import static
    st = static.transient_compile_module(st)
    code = compile(st, srcdata.filename, 'exec')
    importhook.import_cache[file] = code

class ImportProcessor(visitors.InPlaceVisitor):
    examine_functions = True
    
    def visitModule(self, n, path, srcdata):
        ImportFinder().preorder(n.body, os.path.sep.join(srcdata.filename.split(os.path.sep)[:-1]), path)
        ImportTyper().preorder(n.body)
        n.retic_import_env = ImportCollector().preorder(n.body)
    
        return self.dispatch_statements(n.body, path, srcdata)

    def visitClassDef(self, n, *args):
        raise exc.UnimplementedException('class')

    def visitFunctionDef(self, n, path, srcdata):
        ImportFinder().preorder(n.body, os.path.sep.join(srcdata.filename.split(os.path.sep)[:-1]))
        ImportTyper().preorder(n.body)
        n.retic_import_env = ImportCollector().preorder(n.body)

        largs = self.dispatch(n.args, path, srcdata)
        decorator = self.reduce_stmt(n.decorator_list, path, srcdata)
        if self.examine_functions:
            body = self.dispatch_statements(n.body, path, srcdata)
        else: body = self.empty_stmt()
        return self.combine_stmt_expr(body, self.combine_expr(largs, decorator))
        

# Finds the names of modules that will be imported (or have members
# imported from), as well as their levels if relative.
class ImportFinder(visitors.InPlaceVisitor):
    def visitClassDef(self, n, *args):
        pass


    def get_module_definitions(self, directory):
        if os.path.isfile(directory + '.pyi'):
            raise exc.UnimplementedException('Stub file imports not implemented')
        elif os.path.isfile(directory + '.py'):
            return directory + '.py', False
        elif os.path.isdir(directory) and \
             os.path.isfile(directory + os.path.sep + '__init__.py'):
            return directory + os.path.sep + '__init__.py', True
        else:
            return False, False

    def get_module_type(self, directory):
        file, ispackage = self.get_module_definitions(directory)
        if file:
            return get_imported_type(file), ispackage
        else:
            raise exc.StaticTypeError(n, 'Typechecker could not find type definitions for module expected to be at {}'.format(directory))

    def search_paths(self, n, storage_site, targpath, path):

        def find_rootpath(modname):
            # First look for actual .py files, then see if there is a
            # .pyi file in the same directory (as per PEP 484). If
            # there is not, then get the types from the .py file
            # itself. If the .py file is never found, redo the search
            # looking for .pyi files on their own. If a local .pyi
            # file is intended to override a library definition, user
            # needs to write a pragma for this (currently unimplemented)
            for dir in path:
                # Instead, let's do this: iterate over paths until we find
                # the root's location, import it, then loop over the rest
                # of the path importing as we go.
                if os.path.isfile(dir + os.path.sep + modname + '.py'):
                    return dir
                elif os.path.isdir(dir + os.path.sep + modname) and \
                     os.path.isfile(dir + os.path.sep + modname + os.path.sep + '__init__.py'):
                    return dir
            else: # recall that a for's else is executed if the for is not break-ed
                for dir in path:
                    if os.path.isfile(dir + os.path.sep + modname + '.pyi'):
                        return dir
                else: 
                    raise exc.StaticTypeError(n, 'Typechecker could not find type definitions for module {}'.format('.'.join(targpath)))
            

        # First look for actual .py files, then see if there is a
        # .pyi file in the same directory (as per PEP 484). If
        # there is not, then get the types from the .py file
        # itself. If the .py file is never found, redo the search
        # looking for .pyi files on their own. If a local .pyi
        # file is intended to override a library definition, user
        # needs to write a pragma for this (currently unimplemented)

        if targpath[0] in sys.builtin_module_names:
            storage_site.retic_module_type = retic_ast.Dyn()
            storage_site.retic_module_is_package = False
            storage_site.retic_module_package = None
            return

        targ_directory = find_rootpath(targpath[0])
        label = targpath[0]
        type, ispackage = self.get_module_type(targ_directory + os.path.sep + targpath[0])
        targ_directory = targ_directory + os.path.sep + targpath[0]
        lasttype = type

        storage_site.retic_module_package = None
        storage_site.retic_module_is_package = False
        for package in targpath[1:]:
            if not ispackage:
                raise exc.StaticTypeError(n, 'Cannot import module {} from {} because {} is not a package'.format(targpath[0], label, label))
                
            targ_directory = storage_site.retic_module_package = targ_directory + os.path.sep + package
            nexttype, ispackage = self.get_module_type(targ_directory)
            storage_site.retic_module_is_package = ispackage
            if isinstance(lasttype, retic_ast.Module):
                lasttype.exports[package] = nexttype
            else:
                assert isinstance(lasttype, retic_ast.Dyn)
            lasttype = nexttype

        storage_site.retic_module_type = type
        

    def visitImport(self, n, directory, path, *args):
        for alias in n.names:
            targpath = alias.name.split('.')
            # Since multiple files being imported from, stick the file on the individual alias
            self.search_paths(n, alias, targpath, path)

    def visitImportFrom(self, n, directory, path, *args):
        def rectify_import_type(names):
            for alias in names:
                file, _ = self.get_module_definitions(n.retic_module_package + os.path.sep + alias.name)
                if file:
                    type, _ = self.get_module_type(n.retic_module_package + os.path.sep + alias.name)
                    if isinstance(n.retic_module_type, ast.Module):
                        n.retic_module_type.exports[alias.name] = type
            
        if n.level == 0: 
            assert n.module
            # If the module is a package, than any imported name
            # should look for a submodule before getting a value from
            # __init__

            targpath = n.module.split('.')
            # Since only one import, stick the retic_path on the ImportFrom
            self.search_paths(n, n, targpath, path)

            if n.retic_module_is_package:
                rectify_import_type(n.names)
        else: # level > 0 

            # For relative imports, we do the same thing as normal,
            # but we massage the target path and the search
            # paths. First, instead of passing sys.path into
            # search_paths, we pass just the directory we expect the
            # module to reside in, which is (level-1) directories
            # above our current location.  Then we create an import
            # path that combines whatever's in n.module with the end
            # of the current directory
            #
            # One freaky thing is that if n.module is None (i.e. if
            # we're doing some thing like 'from . import k' then the
            # name getting imported can be a module, and it takes
            # priority over values with the same name in
            # __init__.py. If n.module is not none, then it just looks
            # for values on the imported module with that name.
            #
            # Examples: If we are in a file in directory /a/b/c, then
            #
            # from . import k ==> look in ['/a/b/c/'] for module k, if it's not found look in /a/b/c/__init__.py for a value k
            # from .k import j ==> look in ['/a/b/c/'] for module k and look in k for a value j. DO NOT look for a module j.
            # from .. import j ==> look in ['/a/b/'] for module j, if it's not found look in /a/b/__init__.py for a value k
            # from ..k import j ==> look in ['/a/b/'] for module k and look in k for a value j. DO NOT look for a module j.

            endpoint = -(level - 1) if level > 1 else len(directory.split(os.path.sep))

            searchpath = os.path.sep.join(directory.split(os.path.sep)[:endpoint])

            if n.module:
                targpath = n.module.split('.')
                self.search_paths(n, n, targpath, [searchpath])
            else:
                targpath = [searchpath.split(os.path.sep)[-1]]
                searchpath = os.path.sep.join(searchpath.split(os.path.sep)[:-1])
                self.search_paths(n, n, targpath, [searchpath])
                if n.retic_module_is_package:
                    rectify_import_type(n.names)


class ImportTyper(visitors.InPlaceVisitor):
    def visitImport(self, n, *args):
        n.retic_env = {}
        for alias in n.names:
            type = alias.retic_module_type
            asty = type
            attribs = alias.name.split('.')[1:]
            topname = alias.name.split('.')[0]
            label = topname
            if not isinstance(asty, retic_ast.Module) and not isinstance(asty, retic_ast.Dyn):
                raise exc.StaticTypeError(n, 'Import target {} is not a module'.format(label))
            for attrib in attribs:
                try: 
                    asty = asty[attrib]
                except KeyError:
                    raise exc.StaticTypeError(n, 'Import target {} has no member {}'.format(label, attrib))
                label += '.' + attrib
                if not isinstance(asty, retic_ast.Module) and not isinstance(asty, retic_ast.Dyn):
                    raise exc.StaticTypeError(n, 'Import target {} is not a module'.format(label))
            if alias.asname:
                n.retic_env[alias.asname] = asty
            else:
                n.retic_env[topname] = type

    def visitImportFrom(self, n, *args):
        type = n.retic_module_type
        label = '.' * n.level + (n.module.split('.')[0] if n.module else '')
        if not isinstance(type, retic_ast.Module) and not isinstance(type, retic_ast.Dyn):
            raise exc.StaticTypeError(n, 'Import target {} is not a module'.format(label))

        if n.module:
            attribs = n.module.split('.')[1:]
            for attrib in attribs:
                try: 
                    type = type[attrib]
                except KeyError:
                    raise exc.StaticTypeError(n, 'Import target {} has no member {}'.format(label, attrib))
                label += '.' + attrib
                if not isinstance(type, retic_ast.Module) and not isinstance(type, retic_ast.Dyn):
                    raise exc.StaticTypeError(n, 'Import target {} is not a module'.format(label))
        
        n.retic_env = {}
        for alias in n.names:
            if alias.name == '*':
                if isinstance(type, retic_ast.Module):
                    n.retic_env.update(type.exports)
                else:
                    raise exc.StaticTypeError(n, 'The types of import target {} are not statically known, so Reticulated cannot safely import *'.format(label))

            else:
                # Syntactically know that the name does not have a . in it
                key = alias.asname if alias.asname else alias.name
                try: 
                    n.retic_env[key] = type[alias.name]
                except KeyError:
                    raise exc.StaticTypeError(n, 'Import target {} has no member {}'.format(label, alias.name))
            

class ImportCollector(visitors.DictGatheringVisitor):
    def visitClassDef(self, n):
        return {}

    def visitImport(self, n):
        return n.retic_env

    def visitImportFrom(self, n):
        return n.retic_env

class ExportFinder(visitors.DictGatheringVisitor):
    examine_functions = False
    
    def visitcomprehension(self, n, *args):
        return {}

    def visitName(self, n: ast.Name)->typing.Set[ast.expr]:
        if isinstance(n.ctx, ast.Store):
            return { n.id: n.retic_type }
        else: return {}

    def visitFunctionDef(self, n):
        return {n.name : n.retic_type}

    def visitClassDef(self, n):
        raise exc.UnimplementedException('class')

    def visitWith(self, n):
        raise exc.UnimplementedExcpetion('with')

    def visitImport(self, n):
        return n.retic_env

    def visitImportFrom(self, n):
        return n.retic_env