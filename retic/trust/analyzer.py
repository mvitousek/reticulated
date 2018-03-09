from . import grapher
import os    
import numpy

if __name__ == '__main__':
    import argparse, sys
    parser = argparse.ArgumentParser(description='Generate graphs from data set')
    parser.add_argument('--compress', action='store_true',
                        default=False, help='compress graphs')
    parser.add_argument('--just', action='store', nargs=1,
                        default=None, help='only analyze one data set')
    parser.add_argument('--summarize', action='store_true',
                        default=False, help='only generate summaries')
    parser.add_argument('-no', action='store_true',
                        default=False, help='do not show optimized bars in summary')
    parser.add_argument('-nu', action='store_true',
                        default=False, help='do not show unoptimized bars in summary')
    parser.add_argument('--latex', action='store_true',
                        default=False, help='print a latex table')
    parser.add_argument('input', help='directory containing folders for test cases')
    parser.add_argument('output', help='directory to stash graphs')

    args = parser.parse_args(sys.argv[1:])

    dir = args.input
    os.makedirs(args.output, exist_ok=True)
    if args.compress:
        size = (6.2,3)
        compress = True
    else:
        size = (9,6)
        compress = False
        
    summary = {} # interp: {name: data}
    
    for folder in os.listdir(dir):
        folder = os.path.join(dir, folder)
        if os.path.isdir(folder) and (not args.just or folder.strip(os.path.sep).endswith(args.just[0])):
            for file in os.listdir(folder):
                if file.startswith('results') and file.endswith('.csv'):
                    print('({}/{})'.format(folder,file))
                    sc1, sc2, basetime, name, interp = grapher.read_from_csv(os.path.join(folder, file))
                    if not args.summarize:
                        grapher.export_figure(sc1, sc2, basetime, name, interp, os.path.join(args.output, '{}_{}.pdf'.format(name, interp)), size=size, compress=compress)
                    print('\n==={}/{}==='.format(name, interp))
                    data = grapher.summary(sc1, sc2, basetime)
                    
                    if interp in summary:
                        summary[interp][name] = data
                    else:
                        summary[interp] = {name: data}
    
    plt = grapher.plt
    
    def clean(n):
        if 'bm_' in n:
            i = n.index('bm_')
            return clean(n[:i] + n[i+3:])
        if '.noaliases' in n:
            i = n.index('.noaliases')
            return clean(n[:i] + n[i+10:])
        if '.py' in n:
            i = n.index('.py')
            return clean(n[:i] + n[i+3:])
        if '_pypy' in n:
            i = n.index('_pypy')
            return clean(n[:i] + n[i+5:])
        return n.capitalize()
        
    overall_summary = {}
    for interp in summary:
        opt_avg = []
        noopt_avg = []
        full_opt_avg = []
        full_noopt_avg = []

        ticks = []
        py3 = []
        opt = []
        noopt = []
        opt_time = []
        noopt_time = []
        base_times = []
        fig, ax = plt.subplots(figsize=(16,9))
        for name in sorted(summary[interp]):
            data = summary[interp][name]
            ticks.append(clean(name))
            py3.append(1)
            opt.append(data['full_opt_overhead'])
            noopt.append(data['full_noopt_overhead'])
            opt_avg += [data['opt_overhead']] * data['samples']
            noopt_avg += [data['noopt_overhead']] * data['samples']
            opt_time += [data['total_opt_avg']] * data['samples']
            noopt_time += [data['total_noopt_avg']] * data['samples']
            base_times += [data['baseline_time']]
            full_opt_avg += [data['full_opt_overhead']] * data['full_samples']
            full_noopt_avg += [data['full_noopt_overhead']] * data['full_samples']

        ind = numpy.arange(len(ticks))  # the x locations for the groups
        width = 0.25       # the width of the bars

        rects1 = ax.bar(ind, py3, width, color='red')
        legendbar = [rects1[0]]
        legendlabel = [interp.capitalize()]
        pos = ind + width
        if not args.nu:
            rects2 = ax.bar(pos, noopt, width, color='brown')
            legendbar.append(rects2[0])
            legendlabel.append('Unoptimized')
            pos += width
            
        if not args.no:
            rects3 = ax.bar(pos, opt, width, color='blue')
            legendbar.append(rects3[0])
            legendlabel.append('Optimized')
            pos += width
            
        ax.set_ylabel('Relative runtime')
        ax.set_title('Runtime comparison of fully typed Reticulated Python programs to untyped programs running on {}.'.format(interp.capitalize()))
        ax.set_xticks(ind + (pos - ind) / 2)
        ax.set_xticklabels(ticks, rotation=25, ha='right')

        ax.legend(legendbar, legendlabel)
        # ylim = ax.get_ylim()
        # ax.set_ylim(ylim[0], ylim[1] + 1)

        fignote = ''
        if args.nu:
            fignote += 'nu_'
        if args.no:
            fignote += 'no_'
            
        plt.savefig(os.path.join(args.output, '{}_{}summary.pdf'.format(interp, fignote)))
        print('Total opt average', sum(opt_avg)/len(opt_avg))
        print('Total noopt average', sum(noopt_avg)/len(noopt_avg))
        print('Total full opt average', sum(full_opt_avg)/len(full_opt_avg))
        print('Total full noopt average', sum(full_noopt_avg)/len(full_noopt_avg))

        overall_summary[interp] = {
            'total_opt_overhead': sum(opt_avg)/len(opt_avg),
            'total_noopt_overhead': sum(noopt_avg)/len(noopt_avg),
            'total_full_opt_overhead': sum(full_opt_avg)/len(full_opt_avg),
            'total_full_noopt_overhead': sum(full_noopt_avg)/len(full_noopt_avg),
            'total_opt_time': sum(opt_time)/len(opt_time),
            'total_noopt_time': sum(noopt_time)/len(noopt_time),
            'baseline_times': sum(base_times)/len(base_times) 
            }
        print(interp, base_times)

    print('Optimized PyPy/CPython', overall_summary['pypy3']['total_opt_time']/overall_summary['python3']['total_opt_time'])
    print('Unoptimized PyPy/CPython', overall_summary['pypy3']['total_noopt_time']/overall_summary['python3']['total_noopt_time'])
    print('Baseline PyPy/CPython', overall_summary['pypy3']['baseline_times']/overall_summary['python3']['baseline_times'])
    
    if args.latex:
        def display(data_point):
            s = format(data_point, '.2f') + r'$\xtimes$'
            if data_point > 3:
                s = r'\color{tablegray}' + s
            elif data_point <= 1.25:
                s = r'\cellcolor{tableblue}' + s
            return s

        order = [(['pystone_pypy', 'pystone'], 'pystone'), 
                 (['bm_chaos'], 'chaos'), 
                 (['snake'], 'snake'), 
                 (['bm_go'], 'go'), 
                 (['bm_meteor_contest.noaliases'], r'met.\_cont.'),
                 (['suffixtree'], 'suffixtree'),
                 (['bm_float'], 'float'),
                 (['bm_nbody.noaliases'], 'nbody'),
                 (['sieve'], 'sieve'),
                 (['bm_spectral_norm'], r'spect.\_norm')]
        interp_order = ['python3', 'pypy3']
        print(r'''
  \begin{tabular}{|r|rrr|rrr|rrr|rrr|}
    \hline & \multicolumn{6}{l|}{CPython} & \multicolumn{6}{l|}{PyPy} \\
    & \multicolumn{3}{l|}{Unoptimized overheads} & \multicolumn{3}{l|}{Optimized overheads} & \multicolumn{3}{l|}{Unoptimized overheads} & \multicolumn{3}{l|}{Optimized overheads}  \\
    Benchmark  & Mean & Max & Static & Mean & Max & Static  & Mean & Max & Static & Mean & Max & Static\\\hhline{|-|------------|} % jeez''')
        maxnooptmax = {interp: 0 for interp in interp_order}
        maxoptmax = {interp: 0 for interp in interp_order}
        for lookups, name in order:
            print(r'    \texttt{{{}}}'.format(name), end=' ')
            for interp in interp_order:
                for lu in lookups:
                    if '{}.py'.format(lu) in summary[interp]:
                        data = summary[interp]['{}.py'.format(lu)]
                        break
                else:
                    raise Exception('{} not found'.format(name))
                maxnooptmax[interp] = max(maxnooptmax[interp], data['max_noopt_overhead'])
                maxoptmax[interp] = max(maxoptmax[interp], data['max_opt_overhead'])
                print('&', display(data['noopt_overhead']), end=' ')
                print('&', display(data['max_noopt_overhead']), end=' ')
                print('&', display(data['full_noopt_overhead']), end=' ')
                print('&', display(data['opt_overhead']), end=' ')
                print('&', display(data['max_opt_overhead']), end=' ')
                print('&', display(data['full_opt_overhead']), end=' ')
            print(r'\\')
        print(r'    \hline Total', end=' ')
        for interp in interp_order:
            data = overall_summary[interp]
            print('&', display(data['total_noopt_overhead']), end=' ')
            print('&', display(maxnooptmax[interp]), end=' ')
            print('&', display(data['total_full_noopt_overhead']), end=' ')
            print('&', display(data['total_opt_overhead']), end=' ')
            print('&', display(maxoptmax[interp]), end=' ')
            print('&', display(data['total_full_opt_overhead']), end=' ')
        print(r'\\\hline', r'\end{tabular}', sep='\n')

        def sep_latex(interp):
            print('\n', '%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% {} %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n'.format(interp) * 2)
            print(r'''
      \begin{tabular}{|r|rrr|rrr|}
        \hline & \multicolumn{3}{l|}{Unopt. overheads} & \multicolumn{3}{l|}{Opt. overheads}  \\
        Benchmark  & Mean & Max & Static & Mean & Max & Static \\\hhline{|-|------|} % jeez''')
            for lookups, name in order:
                print(r'    \texttt{{{}}}'.format(name), end=' ')
                for lu in lookups:
                    if '{}.py'.format(lu) in summary[interp]:
                        data = summary[interp]['{}.py'.format(lu)]
                        break
                else:
                    raise Exception('{} not found'.format(name))
                print('&', display(data['noopt_overhead']), end=' ')
                print('&', display(data['max_noopt_overhead']), end=' ')
                print('&', display(data['full_noopt_overhead']), end=' ')
                print('&', display(data['opt_overhead']), end=' ')
                print('&', display(data['max_opt_overhead']), end=' ')
                print('&', display(data['full_opt_overhead']), end=' ')
                print(r'\\')
            print(r'    \hline Average', end=' ')
            data = overall_summary[interp]
            print('&', display(data['total_noopt_overhead']), end=' ')
            print('&', display(maxnooptmax[interp]), end=' ')
            print('&', display(data['total_full_noopt_overhead']), end=' ')
            print('&', display(data['total_opt_overhead']), end=' ')
            print('&', display(maxoptmax[interp]), end=' ')
            print('&', display(data['total_full_opt_overhead']), end=' ')
            print(r'\\\hline', r'\end{tabular}', sep='\n')


        for interp in interp_order:
            sep_latex(interp)
        
        




