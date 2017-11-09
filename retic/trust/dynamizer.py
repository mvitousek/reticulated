from .. import visitors, scope, classes, typeparser, retic_ast, copy_visitor, static, exc, typecheck, imports, return_checker, annot_stripper
from . import grapher
import ast, random, os, sys, subprocess, shutil, copy, time
import itertools


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

    # We don't want to mess with lambda arguments, since syntactically
    # they can't be annotated
    def visitLambda(self, n, aliases, *args):
        return []

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
        assert isinstance(ty, retic_ast.ArbAT)
        return 0

def dynamize_node(node, ty, replacement_chance=.1):
    def lhts_elts(node):
        if isinstance(node, ast.Call):
            return node.args[0]
        elif isinstance(node, ast.Subscript):
            return node.slice.value
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
    
def pause(disable_services=True):
    paused = False
    timeout = 60
    while True:
        if os.path.isfile('pause'):
            if not paused:
                paused = True
                if disable_services:
                    print('Pausing and restarting dropbox')
                    try:
                        subprocess.call(['dropbox.py', 'start'])
                        subprocess.call(['sudo', '-k', 'service', 'plexmediaserver', 'start'])
                    except OSError:
                        pass
                else:
                    print('Pausing')

                with open('pause', 'r') as pfile:
                    try:
                        timeout = int(pfile.read().strip())
                    except:
                        pass

            time.sleep(timeout)
        elif paused:
            if disable_services:
                try:
                    print('Ending pause and stopping dropbox')
                    subprocess.call(['dropbox.py', 'stop'])
                    subprocess.call(['sudo', '-k', 'service', 'plexmediaserver', 'stop'])
                    time.sleep(10)
                except OSError:
                    pass
            else:
                print('Ending pause')
            break
        else: break
            
                

def analyze(files, basefile, basename, dir, interp, optimized):
    def test_file(file, interp):
        def run_file():
            try:
                pause()
                print('Testing', file, 'with', interp)
                oresult = subprocess.check_output([interp, file], 
                                                  stderr=subprocess.STDOUT).decode('utf-8').strip()
            except Exception as e:
                print('Test error')
                exc = e.output.decode('utf-8').strip()
                printed = '\n'.join(line for line in exc.split('\n'))
                print(printed)
                raise
            return oresult.split('\n')

        if basename.startswith('pystone'):
            pystone_results = [float(result[0].split()[6]) for result in [run_file() for i in range(10)]]
            return sum(pystone_results)/len(pystone_results)
        else:
            ts = [float(t) for t in run_file() if not t.startswith('Avg')]
            return sum(ts)/len(ts)

    print('Analyzing', basename)
    try:
        try:
            print('Stopping dropbox')
            subprocess.call(['dropbox.py', 'stop'])
            subprocess.call(['sudo', '-k', 'service', 'plexmediaserver', 'stop'])
            time.sleep(10)
        except OSError:
            pass
        
        

        for interp in interp:
            times = []
            pcts = {}
        
            try:
                os.remove(os.path.join(dir, 'results_{}.csv'.format(''.join(interp.split(os.path.sep)))))
            except OSError:
                pass
            try:
                os.remove(os.path.join(dir, 'results_{}.csv.temp'.format(''.join(interp.split(os.path.sep)))))
            except OSError:
                pass
            try:
                os.remove(os.path.join(dir, 'results_{}.pdf'.format(''.join(interp.split(os.path.sep)))))
            except OSError:
                pass

            with open(os.path.join(dir, 'results_{}.csv'.format(''.join(interp.split(os.path.sep)))), 'w') as wfile:
                basetime = test_file(basefile, interp)
                print('\n-----baseline-----')
                print(basetime)

                for i, ifiles in enumerate(files):
                    
                    pct = int(100 * (((len(files) - 1) - i) / (len(files) - 1)))
                    pcts[i] = pct
                    l_itimes = []
                    r_itimes = []
                    times.append((l_itimes, r_itimes))
                    for l_file, r_file in ifiles:
                        l_itimes.append(test_file(l_file, interp))
                        if r_file is not None:
                            assert optimized == 'BOTH'
                            r_itimes.append(test_file(r_file, interp))
                    print('\n-----{}%-----'.format(pct))
                    lavg = sum(l_itimes)/len(l_itimes)
                    print('First Avg:', lavg)
                    if r_itimes:
                        ravg = sum(r_itimes)/len(r_itimes)
                        print('Second Avg:', ravg)

                print(basename, interp, optimized, sep=',', file=wfile)
                print('baseline', basetime, sep=',', file=wfile)

                xs = []
                y1s = []
                y2s = []
                ids = []
                for i, (lit, rit) in enumerate(times):
                    for j, (lv, rv) in enumerate(itertools.zip_longest(lit, rit)):
                        xs.append(pcts[i])
                        y1s.append(lv)
                        ids.append(j)
                        print(pcts[i], lv, sep=',', end=',', file=wfile)
                        if rv is not None:
                            assert optimized == 'BOTH'
                            y2s.append(rv)
                            print(rv, end=',', file=wfile)
                        print(j, file=wfile)
            try:
                shutil.copy2(os.path.join(dir, 'results_{}.csv.temp'.format(''.join(interp.split(os.path.sep)))), 
                             os.path.join(dir, 'results_{}.csv'.format(''.join(interp.split(os.path.sep)))))
                os.remove(os.path.join(dir, 'results_{}.csv.temp'.format(''.join(interp.split(os.path.sep)))))
            except FileNotFoundError:
                pass
            grapher.export_figure((xs, y1s, ids), (xs, y2s, ids) if optimized == 'BOTH' else None,
                                  basetime, basename, interp, 
                                  os.path.join(dir, 'results_{}.pdf'.format(''.join(interp.split(os.path.sep)))))
    finally:
        try:
            print('Restarting dropbox')
            subprocess.call(['dropbox.py', 'start'])
            subprocess.call(['sudo', '-k', 'service', 'plexmediaserver', 'start'])
        except OSError:
            pass

def analyze_existing(basename, dir, interp, optimized):
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
        elif sub.startswith(basename[:-3]) and sub.endswith('.untyped.py'):
            basefile = subpath
    files = []
    for sub in reversed(sorted(sub_ints)):
        ifiles = []
        rfiles = []
        for prog in os.listdir(os.path.join(dir, str(sub))):
            if prog.startswith(basename[:-3]) and prog.endswith('.py') and not prog.endswith('.original.py'):
                if optimized == 'BOTH':
                    if prog.split('.')[-2] == 'opt':
                        ifiles.append(os.path.join(dir, str(sub), prog))
                    elif prog.split('.')[-2] == 'noopt':
                        rfiles.append(os.path.join(dir, str(sub), prog))
                    else:
                        raise Exception()
                else:
                    ifiles.append(os.path.join(dir, str(sub), prog))
        assert len(ifiles) <= 10 # Sorting won't work if we have a 2+ digit number
        assert len(rfiles) <= 10
        
        files.append(list(itertools.zip_longest(list(sorted(ifiles)), list(sorted(rfiles)))))
    analyze(files, basefile, basename, dir, interp, optimized)     

def regraph(interps, dir):
    for interp in interps:
        interppath = os.path.join(dir, 'results_{}.csv'.format(''.join(interp.split(os.path.sep))))
        if os.path.isfile(interppath):
            sc1, sc2, basetime, basename, interp = grapher.read_from_csv(interppath)
            grapher.export_figure(sc1, sc2, basetime, basename, interp, os.path.join(dir, 'results_{}.pdf'.format(''.join(interp.split(os.path.sep)))))
        else: 
            print('No results file for interpreter {}: file {} does not exist'.format(interp, interppath))
    
    
dir_ = dir
def lattice_test_module(st, srcdata, dir, interp, optimize, topenv=None, exit=True):
    assert os.path.basename(srcdata.filename)[-3:] == '.py'
    
    try:
        # Determine the types of imported values, by finding and
        # typechecking the modules being imported.
        os.makedirs(dir, exist_ok=True)
        util = os.path.join(os.path.dirname(srcdata.filename), 'util.py')
        try:
            shutil.copy2(util, dir)
        except FileNotFoundError:
            pass
        base = annot_stripper.AnnotationStripper().preorder(st)
        base_filename = os.path.join(dir, os.path.basename(srcdata.filename)[:-3] + '.untyped' + os.path.basename(srcdata.filename)[-3:])
        
        with open(base_filename, 'w', encoding='utf-8') as write:
            static.emit_module(base, file=write, imports=False)
        
        imports.ImportProcessor().preorder(st, sys.path, srcdata)
        asts, maxweight = dynamize(st)
        files = []
        for i, samples in enumerate(asts):
            pct = int(100 * (((len(asts) - 1) - i) / (len(asts) - 1)))
            print(pct, 'percent typed')
            os.makedirs(os.path.join(dir, str(pct)), exist_ok=True)
            util = os.path.join(os.path.dirname(srcdata.filename), 'util.py')
            try:
                shutil.copy2(util, os.path.join(dir, str(pct)))
            except FileNotFoundError:
                pass
            ifiles = []
            files.append(ifiles)
            for j, st in enumerate(samples):
                pause(disable_services=False)

                filename = os.path.join(dir, str(pct), os.path.basename(srcdata.filename)[:-3] + str(j) + os.path.basename(srcdata.filename)[-3:])
                with open(filename + '.original.py', 'w', encoding='utf-8') as write:
                    static.emit_module(st, file=write, imports=False)
                # Gather the bound variables for every scope
                print('Typechecked', srcdata.filename, 'at {}%'.format(pct), 'typed, sample', j)
                scope.ScopeFinder().preorder(st, topenv)
                # Perform most of the typechecking
                typecheck.Typechecker().preorder(st)
                # Make sure that all functions return and that all returned
                # values match the return type of the calling function
                return_checker.ReturnChecker().preorder(st)
                
                if optimize == 'BOTH':
                    sts = [('OPT', filename[:-3] + '.opt' + filename[-3:], copy_visitor.CopyVisitor(examine_functions=True).preorder(st)), 
                           ('NOOPT', filename[:-3] + '.noopt' + filename[-3:], st)]
                else:
                    sts = [(optimize, filename, st), (None, None, None)]

                lfiles = []
                ifiles.append(lfiles)
                for test_optimize, filename, st in sts:
                    if st is None:
                        assert test_optimize is None and filename is None
                        lfiles.append(None)
                    else:
                        st = static.transient_compile_module(st, test_optimize == 'OPT')
                        lfiles.append(filename)
                        with open(filename, 'w', encoding='utf-8') as write:
                            static.emit_module(st, file=write)
        analyze(files, base_filename, os.path.basename(srcdata.filename), dir, interp, optimize)
    except exc.StaticTypeError as e:
        exc.handle_static_type_error(e, srcdata, exit=exit)
    except exc.MalformedTypeError as e:
        exc.handle_malformed_type_error(e, srcdata, exit=exit)
    else:
        return st

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Analyze Reticulated perfomance lattice')
    opts = parser.add_mutually_exclusive_group()
    opts.add_argument('-n', '--no-opt', dest='optimize', action='store_const', const='NOOPT',
                        help='exclusively do not optimize transient checks')
    opts.add_argument('-o', '--opt', dest='optimize', action='store_const', const='OPT',
                        help='exclusively optimize transient checks')
    opts.set_defaults(optimize='BOTH')
    work = parser.add_mutually_exclusive_group()
    work.add_argument('-e', '--existing', dest='work', action='store_const', 
                        const='EXISTING', help='analyze already existing files in directory')
    work.add_argument('-r', '--regraph', dest='work', action='store_const', 
                        const='REGRAPH', help='regenerate graphs based on existing files in directory')
    work.set_defaults(work='FULL')
    parser.add_argument('interpreter', nargs='+', action='store', 
                        type=str, help='test with the Python3 interpeters given')
    parser.add_argument('program', help='a Python program to be executed (.py extension required)')
    parser.add_argument('test_dir', help='a directory in which to store generated programs and performance results')

    args = parser.parse_args(sys.argv[1:])
    if args.work == 'EXISTING':
        analyze_existing(os.path.basename(args.program), args.test_dir, args.interpreter, args.optimize)
    elif args.work == 'REGRAPH':
        regraph(args.interpreter, args.test_dir)
    else:
        try:
            with open(args.program, 'r', encoding='utf-8') as program:
                sys.path.insert(1, os.path.sep.join(os.path.abspath(args.program).split(os.path.sep)[:-1]))

                st, srcdata = static.parse_module(program)

                lattice_test_module(st, srcdata, args.test_dir, args.interpreter, args.optimize)
        except IOError as e:
            print(e)

if __name__ == '__main__':
    main()
