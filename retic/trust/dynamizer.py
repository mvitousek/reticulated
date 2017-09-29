from .. import visitors, scope, classes, typeparser, retic_ast, copy_visitor, static, exc, typecheck, imports, return_checker 
import ast, random, os, sys, subprocess, shutil, copy, time

def dyn(n):
    return ast.copy_location(ast.Name(id='Any', ctx=ast.Load()), n)
    
def fix_location(new, old):
    ast.copy_location(new, old)
    ast.fix_missing_locations(new)
    return new

def class_aliases(stmts):
    cls = classes.ClassFinder().preorder(stmts)
    classenv = { name: cls[name].type for name in cls }
    typeenv = { name: retic_ast.Instance(classenv[name]) for name in cls }
    return typeenv

# Since it uses n.retic_import_aliases, this has to fire after the import handler.
class AnnotationFinder(visitors.ListGatheringVisitor):
    examine_functions = True
    def visitModule(self, n, *args):
        aliases = n.retic_import_aliases.copy()
        aliases.update(class_aliases(n.body))
        aliases = scope.gather_aliases(n, aliases)
        return super().visitModule(n, aliases, *args)

    def visitarg(self, n, aliases, *args):
        if not n.annotation:
            n.annotation = dyn(n)
        return [(n.annotation, typeparser.typeparse(n.annotation, aliases))]
           
    def visitFunctionDef(self, n, aliases, *args):
        aliases = aliases.copy()
        aliases.update(n.retic_import_aliases.copy())
        aliases.update(class_aliases(n.body))
        aliases = scope.gather_aliases(n, aliases)
        res = super().visitFunctionDef(n, aliases, *args)
        if n.name != '__init__':
            if not n.returns:
                n.returns = dyn(n)
            return res + [(n.returns, typeparser.typeparse(n.returns, aliases))]
        else:
            return res

    def visitClassDef(self, n, aliases, *args):
        res = super().visitClassDef(n, aliases, *args)
        for dec in n.decorator_list:
            if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Name) and \
               dec.func.id in {'fields', 'members'}:
                res += [(v, typeparser.typeparse(v, aliases)) for v in dec.args[0].values]
        return res

class AnnotationReplacer(copy_visitor.CopyVisitor):
    examine_functions = True

    def visitFunctionDef(self, n, subst, *args):
        if n.returns in subst:
            returns = subst[n.returns][1]
        else:
            returns = None
        n = super().visitFunctionDef(n, subst, *args)
        if returns:
            n.returns = returns
        return n
        
    def visitarg(self, n, subst, *args):
        if n.annotation in subst:
            annotation = subst[n.annotation][1]
        else:
            annotation = None
        n = super().visitarg(n, subst, *args)
        if annotation:
            n.annotation = annotation
        return n

    def dispatch(self, n, subst, *args):
        if n in subst:
            return subst[n][1]
        else:
            return super().dispatch(n, subst, *args)

def weight(ty):
    if any(isinstance(ty, cls) for cls in {retic_ast.List, retic_ast.HTuple, retic_ast.Set}):
        return 1 + weight(ty.elts)
    elif isinstance(ty, retic_ast.Tuple):
        return 1 + sum(weight(elt) for elt in ty.elts)
    elif isinstance(ty, retic_ast.Dict):
        return 1 + weight(ty.keys) + weight(ty.values)
    elif isinstance(ty, retic_ast.Function):
        return 1 + param_weight(ty.froms) + weight(ty.to)
    elif isinstance(ty, retic_ast.Structural):
        return 1 + sum(weight(ty.members[v]) for v in ty.members)
    elif isinstance(ty, retic_ast.Dyn):
        return 0
    else:
        return 1
def param_weight(ty):
    if isinstance(ty, retic_ast.PosAT):
        return sum(weight(arg) for arg in ty.types)
    else:
        return 0

def dynamize_node(node, ty, replacement_chance=.1):
    def lhts_elts(node):
        if isinstance(node, ast.Call):
            return node.args[0]
        elif isinstance(node, ast.Subscript):
            return node.slice.value.elts[0]
    def tuple_elts(node):
        if isinstance(node, ast.Tuple):
            return node.elts
        elif isinstance(node, ast.Call):
            return node.args
        elif isinstance(node, ast.Subscript):
            return node.slice.value.elts
    def dict_keys(node):
        if isinstance(node, ast.Call):
            return node.args[0]
        elif isinstance(node, ast.Subscript):
            return node.slice.value.elts[0]
    def dict_vals(node):
        if isinstance(node, ast.Call):
            return node.args[1]
        elif isinstance(node, ast.Subscript):
            return node.slice.value.elts[1]
    def fn_to(node):
        if isinstance(node, ast.Call):
            return node.args[1]
        elif isinstance(node, ast.Subscript):
            return node.slice.value.elts[1]
    def fn_args(node):
        if isinstance(node, ast.Call):
            return node.args[0].elts
        elif isinstance(node, ast.Subscript):
            return node.slice.value.elts[0].elts
    def struct_keys(node):
        return node.keys
    def struct_vals(node):
        return node.values
        
    if random.random() < replacement_chance:
        return weight(ty), dyn(node)
    elif any(isinstance(ty, cls) for cls in {retic_ast.List, retic_ast.HTuple, retic_ast.Set}):
        w, elts = dynamize_node(lhts_elts(node), ty.elts)
        if w > 0:
            if isinstance(ty, retic_ast.List):
                return w, fix_location(ast.Subscript(value=ast.Name(id='List', ctx=ast.Load()),
                                                     slice=ast.Index(value=elts), ctx=ast.Load()), node)
            elif isinstance(ty, retic_ast.Set):
                return w, fix_location(ast.Subscript(value=ast.Name(id='Set', ctx=ast.Load()),
                                                     slice=ast.Index(value=elts), ctx=ast.Load()), node)
            elif isinstance(ty, retic_ast.HTuple):
                return w, fix_location(ast.Subscript(value=ast.Name(id='Tuple', ctx=ast.Load()),
                                                     slice=ast.Index(value=ast.Tuple(elts=[elts, ast.Ellipsis()], ctx=ast.Load())), 
                                                     ctx=ast.Load()), node)
        else:
            return 0, node
    elif isinstance(ty, retic_ast.Tuple):
        ws, elts = zip(*[dynamize_node(elt, ty) for elt, ty in zip(tuple_elts(node), ty.elts)])
        w = sum(ws)
        if w > 0:
            return w, fix_location(ast.Subscript(value=ast.Name(id='Tuple', ctx=ast.Load()),
                                                 slice=ast.Index(value=ast.Tuple(elts=list(elts), ctx=ast.Load())), 
                                                 ctx=ast.Load()), node)
        else:
            return 0, node
    elif isinstance(ty, retic_ast.Dict):
        wk, keys = dynamize_node(dict_keys(node), ty.keys)
        wv, vals = dynamize_node(dict_vals(node), ty.values)
        if wk + wv > 0:
            return wk + wv, fix_location(ast.Subscript(value=ast.Name(id='Dict', ctx=ast.Load()),
                                                       slice=ast.Index(value=ast.Tuple(elts=[keys, vals], ctx=ast.Load())), 
                                                       ctx=ast.Load()), node)
        else:
            return 0, node
    elif isinstance(ty, retic_ast.Function):
        wt, to = dynamize_node(fn_to(node), ty.to)
        if isinstance(ty.froms, retic_ast.PosAT):
            if len(fn_args(node)) > 0:
                was, args = zip(*[dynamize_node(elt, ty) for elt, ty in zip(fn_args(node), ty.froms.types)])
                wa = sum(was)
            else:
                args = []
                wa = 0
            if wt + wa > 0:
                return wt + wa, fix_location(ast.Subscript(value=ast.Name(id='Callable', ctx=ast.Load()),
                                                           slice=ast.Index(value=ast.Tuple(elts=[ast.List(elts=list(args), ctx=ast.Load), to], 
                                                                                           ctx=ast.Load())), 
                                                           ctx=ast.Load()), node)
            else:
                return 0, node
        else:
            assert isinstance(ty.froms, retic_ast.ArbAT)
            if wt > 0:
                return wt, fix_location(ast.Subscript(value=ast.Name(id='Callable', ctx=ast.Load()),
                                                      slice=ast.Index(value=ast.Tuple(elts=[ast.Ellipsis(), to], 
                                                                                      ctx=ast.Load())), 
                                                      ctx=ast.Load()), node)
            else:
                return 0, node
    elif isinstance(ty, retic_ast.Structural):
        mems = [(k, dynamize_node(v, ty.members[k.s])) for k, v in zip(struct_keys(node), struct_vals(node))]
        w = 0
        keys = []
        vals = []
        for k, (we, v) in mems:
            w += we
            keys.append(k)
            vals.append(v)
        if w > 0:
            return w, fix_location(ast.Dict(keys=keys, values=vals), node)
        else:
            return 0, node
    else:
        return 0, node

def dynamize(node, samples_per_unit=10, max_units=100):
    annots = AnnotationFinder().preorder(node)
    maxweight = sum(weight(a[1]) for a in annots)
    
    unit_step = max(1, int((maxweight+1) / (max_units+1)))

    asts = [[node]] + [[] for i in range(1, maxweight+1, unit_step)]

    for i, unit in enumerate(range(1, maxweight + 1, unit_step)):
        unit_asts = asts[i+1]
        for sample in (range(samples_per_unit) if unit != maxweight else [0]):
            sample_annots = annots[:]
            subst = {}
            fuel = 0
            while fuel < unit:
                target = sample_annots[random.randrange(len(sample_annots))]
                if target[0] in subst:
                    v, _ = subst[target[0]]
                    if v >= weight(target[1]):
                        continue
                w, new_node = dynamize_node(target[0], target[1])
                if target[0] in subst:
                    v, _ = subst[target[0]]
                    if w > v and fuel + w - v < unit + unit_step:
                        fuel += w - v
                        subst[target[0]] = (w, new_node)
                        if w >= weight(target[1]):
                            sample_annots.remove(target)
                else:
                    if w > 0 and fuel + w < unit + unit_step:
                        fuel += w
                        subst[target[0]] = (w, new_node)
                        if w >= weight(target[1]):
                            sample_annots.remove(target)
            ast = AnnotationReplacer().preorder(node, subst)
            print('Sample with {}/{} weight generated'.format(fuel, maxweight))
            unit_asts.append(ast)
    
    # Sanity check:
    # for i, samples in enumerate(asts):
    #     for sample in samples:
    #         sample_annots = AnnotationFinder().preorder(sample)
    #         sample_weight = sum(weight(a[1]) for a in sample_annots)
    #         assert (i * unit_step) <= (maxweight - sample_weight) < ((i + 1) * unit_step), '{}: {} <= {} < {} false'.format(i, (i * unit_step), (maxweight - sample_weight), ((i + 1) * unit_step))
            
    return asts, maxweight
    
def analyze(files, basename, dir):
    times = []
    pcts = {}
    try:
        try:
            print('Stopping dropbox')
            subprocess.call(['dropbox.py', 'stop'])
            time.sleep(10)
        except OSError:
            pass
        try:
            os.remove(os.path.join(dir, 'results.csv'))
        except OSError:
            pass
        for i, ifiles in enumerate(files):
            pct = int(100 * (((len(files) - 1) - i) / (len(files) - 1)))
            pcts[i] = pct
            itimes = []
            times.append(itimes)
            for file in ifiles:
                try:
                    print('Testing', file)
                    oresult = subprocess.check_output(['python3'] + [file], 
                                                      stderr=subprocess.STDOUT).decode('utf-8').strip()
                except Exception as e:
                    exc = e.output.decode('utf-8').strip()
                    printed = '\n'.join(line for line in exc.split('\n'))
                    print(printed)
                    raise
                result = '\n'.join(line for line in oresult.split('\n'))
                if basename.startswith('pystone'):
                    itimes.append(float(result.split()[6]))
                else:
                    ts = [float(t) for t in result.split('\n') if not t.startswith('Avg')]
                    itimes.append(sum(ts)/len(ts))
            print('\n-----{}%-----'.format(pct))
            avg = sum(itimes)/len(itimes)
            print('Avg:', avg)
        import itertools
        table = itertools.zip_longest(*times)
        with open(os.path.join(dir, 'results.csv'), 'w') as file:
            print(basename, 'performance', file=file)
            print(*[pcts[i] for i in range(len(times))], file=file, sep=',')
            for line in table:
                print(*[pt if pt else '' for pt in line], file=file, sep=',')
            print('\n\n\n', file=file)
            for i, it in enumerate(times):
                for j, v in enumerate(it):
                    print(pcts[i], v, j, sep=',', file=file)
    finally:
        try:
            print('Restarting dropbox')
            subprocess.call(['dropbox.py', 'start'])
        except OSError:
            pass
        
        

def analyze_existing(dir):
    basename = os.path.basename(dir)
    try:
        basename = basename[:basename.index('_noopt')]
    except ValueError:
        pass
    subs = os.listdir(dir)
    sub_ints = []
    for sub in os.listdir(dir):
        subpath = os.path.join(dir, sub)
        if os.path.isdir(subpath):
            try: 
                pct = int(sub)
                sub_ints.append(pct)
            except ValueError:
                continue
    files = []
    for sub in reversed(sorted(sub_ints)):
        ifiles = []
        for prog in os.listdir(os.path.join(dir, str(sub))):
            if prog.startswith(basename) and prog.endswith('.py') and not prog.endswith('.original.py'):
                ifiles.append(os.path.join(dir, str(sub), prog))
        files.append(sorted(ifiles))
    analyze(files, basename, dir)     
    
    
dir_ = dir
def lattice_test_module(st, srcdata, optimize, dir, topenv=None, exit=True):
    try:
        # Determine the types of imported values, by finding and
        # typechecking the modules being imported.
        imports.ImportProcessor().preorder(st, sys.path, srcdata)
        asts, maxweight = dynamize(st)
        files = []
        for i, samples in enumerate(asts):
            pct = int(100 * (((len(asts) - 1) - i) / (len(asts) - 1)))
            print(pct, 'percent typed')
            os.makedirs(os.path.join(dir, str(pct)), exist_ok=True)
            util = os.path.join(os.path.dirname(srcdata.filename), 'util.py')
            try:
                shutil.copy2(util, os,path.join(dir, str(pct)))
            except FileNotFoundError:
                pass
            ifiles = []
            files.append(ifiles)
            for j, st in enumerate(samples):
                filename = os.path.join(dir, str(pct), os.path.basename(srcdata.filename)[:-3] + str(j) + os.path.basename(srcdata.filename)[-3:])
                with open(filename + '.original.py', 'w') as write:
                    static.emit_module(st, write)
                #print('Processed imports for', srcdata.filename)
                # Gather the bound variables for every scope
                scope.ScopeFinder().preorder(st, topenv)
                # Perform most of the typechecking
                typecheck.Typechecker().preorder(st)
                # Make sure that all functions return and that all returned
                # values match the return type of the calling function
                return_checker.ReturnChecker().preorder(st)
                print('Typechecked', srcdata.filename)
                st = static.transient_compile_module(st, optimize)
                ifiles.append(filename)
                with open(filename, 'w') as write:
                    static.emit_module(st, write)
        analyze(files, os.path.basename(srcdata.filename), dir)
    except exc.StaticTypeError as e:
        exc.handle_static_type_error(e, srcdata, exit=exit)
    except exc.MalformedTypeError as e:
        exc.handle_malformed_type_error(e, srcdata, exit=exit)
    else:
        return st

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Analyze Reticulated perfomance lattice')
    parser.add_argument('-n', '--no-opt', dest='optimize', action='store_false', 
                        default=True, help='do not optimize transient checks')
    parser.add_argument('-e', '--existing', dest='existing', action='store_true', 
                        default=False, help='analyze already existing files in directory')
    parser.add_argument('program', help='a Python program to be executed (.py extension required)', default=None)
    parser.add_argument('test_dir', help='a directory in which to store generated programs and performance results', default=None)

    args = parser.parse_args(sys.argv[1:])
    if args.existing:
        analyze_existing(args.test_dir)
    else:
        try:
            with open(args.program, 'r') as program:
                sys.path.insert(1, os.path.sep.join(os.path.abspath(args.program).split(os.path.sep)[:-1]))

                st, srcdata = static.parse_module(program)

                lattice_test_module(st, srcdata, args.optimize, args.test_dir)
        except IOError as e:
            print(e)

if __name__ == '__main__':
    main()
