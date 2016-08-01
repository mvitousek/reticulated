from . import visitors, exc, typing, retic_ast
import os.path, sys, ast

path = sys.path

import_cache = {}

def get_imported_type(file, srcdata):
    if file is None:
        return retic_ast.Dyn()
    elif file in import_cache:
        return import_cache[file]
    else:
        with open(file, 'r') as data:
            st, srcdata = srcdata.parser(data)
        st = srcdata.typechecker(st, srcdata)
        import_cache[file] = st.retic_type
        return st.retic_type
            

class ImportProcessor(visitors.InPlaceVisitor):
    examine_functions = True
    
    def visitModule(self, n, path, srcdata):
        ImportFinder().preorder(n.body, os.path.sep.join(srcdata.filename.split(os.path.sep)[:-1]), path)
        ImportTyper().preorder(n.body, srcdata)
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

    def search_paths(self, n, storage_site, targpath, path):
        # First look for actual .py files, then see if there is a
        # .pyi file in the same directory (as per PEP 484). If
        # there is not, then get the types from the .py file
        # itself. If the .py file is never found, redo the search
        # looking for .pyi files on their own. If a local .pyi
        # file is intended to override a library definition, user
        # needs to write a pragma for this (currently unimplemented)
        for dir in path:
            # We only need to search for the first part of the
            # import target: for import a.x, we just find a,
            # typecheck it, and get the x element out of it.
            if os.path.isfile(dir + os.path.sep + targpath + '.py'):
                if os.path.isfile(dir + os.path.sep + targpath + '.pyi'):
                    raise exc.UnimplementedException('Stub file imports not implemented')
                else:
                    storage_site.retic_file = (dir + os.path.sep + targpath + '.py')
                    break
        else: # recall that a for's else is executed if the for is not break-ed
            for dir in path:
                if os.path.isfile(dir + os.path.sep + targpath + '.pyi'):
                    raise exc.UnimplementedException('Stub file imports not implemented')
                    break
            else:
                if targpath in sys.builtin_module_names:
                    storage_site.retic_file = None
                else: 
                    raise exc.StaticTypeError(n, 'Typechecker could not find type definitions for module {}'.format(targpath))
        

    def visitImport(self, n, directory, path, *args):
        for alias in n.names:
            targpath = alias.name.split('.')[0]
            # Since multiple files being imported from, stick the file on the individual alias
            self.search_paths(n, alias, targpath, path)

    def visitImportFrom(self, n, directory, path, *args):
        if n.level == 0: 
            targpath = n.module.split('.')[0]
            # Since only one import, stick the retic_path on the ImportFrom
            self.search_paths(n, n, targpath, path)
        else: # level > 0
            targpath = '__init__'
            searchpath = os.path.sep.join(directory.split(os.path.sep)[:-(level - 1)])
            if os.path.isfile(searchpath + os.path.sep + targpath + '.pyi'):
                raise exc.UnimplementedException('Stub file imports not implemented')
            elif os.path.isfile(searchpath + os.path.sep + targpath + '.py'):
                n.retic_file = (searchpath + os.path.sep + targpath + '.py')
            else: raise exc.StaticTypeError(n, 'Reticulated could not find type definitions for module {}'.format(searchpath))


class ImportTyper(visitors.InPlaceVisitor):
    def visitImport(self, n, srcdata, *args):
        n.retic_env = {}
        for alias in n.names:
            type = get_imported_type(alias.retic_file, srcdata)
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

    def visitImportFrom(self, n, srcdata, *args):
        type = get_imported_type(n.retic_file, srcdata)
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
                if not isinstance(asty, retic_ast.Module) and not isinstance(asty, retic_ast.Dyn):
                    raise exc.StaticTypeError(n, 'Import target {} is not a module'.format(label))
        
        n.retic_env = {}
        for alias in n.names:
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
