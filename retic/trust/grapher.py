# Note imports at the bottom of the file: if we're running headless,
# we need to call 'matplotlib.use('Agg')' before importing
# matplotlib.pyplot (which is imported as plt).

FST_MARKER = '^'
FST_COLOR = 'blue' # Blue
SND_MARKER = 'o'
SND_COLOR = 'brown' # Red
LINE_COLOR = 'red'
ALPHA = 1

def make_figure(sc1, sc2, linepos, name, interp, *, zoom=False, show_ids=True, size=(9,6), compress=False, show_scale=True, filter=.5):
    ct = int(1/filter)
    
    fig = plt.figure(figsize=size)
    x1, y1, id1 = sc1

    if sc2 is not None:
        x2, y2, id2 = sc2
        l2 = plt.scatter(x2[::ct], y2[::ct], marker=SND_MARKER, c='', edgecolor=SND_COLOR, alpha=ALPHA, picker=show_ids)
    
    l1 = plt.scatter(x1[::ct], y1[::ct], marker=FST_MARKER, c=FST_COLOR, edgecolor='', alpha=ALPHA, picker=show_ids)

    line = plt.axhline(y=linepos, color=LINE_COLOR, lw=2, ls='--')
    if not compress:
        if sc2 is not None:
            plt.legend((line, l1, l2), ('Baseline performance', 'Optimized sample', 'Unoptimized sample'), scatterpoints=1, loc=2)
        else:
            plt.legend((line, l1), ('Baseline performance', 'Sample',), scatterpoints=1, loc=2)
        plt.xlabel('Static typing percentage')
        plt.ylabel('Execution time (seconds)')
        plt.title('Execution times for {} under {}'.format(name, interp))
        plt.legend()
    else:
        plt.ylabel('Execution time (s)')
        plt.xlabel('Static typing percentage')
        # if sc2 is not None:
        #     fig_legend.legend((line, l1, l2), ('Baseline performance', 'Optimized sample', 'Unoptimized sample'), scatterpoints=1)
        # else:
        #     fig_legend.legend((line, l1), ('Baseline performance', 'Sample',), scatterpoints=1, loc='center', frameon=False)
        # fig_legend.savefig('legend.pdf')
        
        
    axes = plt.gca()
    axes.set_xlim((0, 100))
    if not zoom:
        ymin, ymax = axes.get_ylim()
        if not compress:
            ymax = ymax + ymin / 2
        ymin = 0
    else:
        ymin = min(y1)
        ymax = max(y1)
        if sc2 is not None:
            ymin = min(ymin, *y2)
            ymax = max(ymax, *y2)
        dist = ymax - ymin
        ymin = ymin-dist/5
        ymax = ymax+dist/5
        
    axes.set_ylim((ymin, ymax))
        
    if show_scale:
        axes2 = axes.twinx()
        denom = linepos if linepos else 1
        axes2.set_ylim((ymin/denom, ymax/denom))
        axes2.set_ylabel('Proportional overhead')
        
    if compress:
        plt.tight_layout()

    text = None
    lastcoords = (-1,-1)
    lastcount = 0
    def show_label(event):
        nonlocal text, lastcoords, lastcount
        try:
            ind = event.ind
        except AttributeError:
            if text is not None:
                text.remove()
                text = None
            lastcoords = (-1,-1)
            lastcount = 0
            event.canvas.draw()
            return
        xy = event.artist.get_offsets()
        firstgo = True
        print('--------')
        for x,y in xy[ind]:
            axis = None
            for vx, vy, id in zip(x1[::ct], y1[::ct], id1[::ct]):
                if int(x) == vx and y == vy:
                    print('Optimized sample {} at {}%'.format(id, vx))
                    axis = 'Optimized'
                    break
            else: # If break is not hit
                if sc2 is not None:
                    for vx, vy, id in zip(x2[::ct], y2[::ct], id2[::ct]):
                        if int(x) == vx and y == vy:
                            print('Unoptimized sample {} at {}%'.format(id, vx))
                            axis = 'Unoptimized'
                            break
                    else:
                        print('Key not found')
                else: 
                    print('Key not found')
            if firstgo and axis is not None:
                if text is not None:
                    text.remove()
                s = '{} sample {} at {}%'.format(axis, id, vx)
                if lastcoords == (event.mouseevent.x, event.mouseevent.y):
                    prevcount = lastcount
                else:
                    prevcount = 0
                if len(xy[ind]) + prevcount > 1:
                    s += ', and {} other{}'.format(len(xy[ind]) + prevcount - 1, 's' if len(xy[ind]) + prevcount > 2 else '')
                text = plt.text(.95, .05, s, fontsize=12, horizontalalignment='right', verticalalignment='bottom', transform=axes.transAxes, picker=True)
                lastcoords = (event.mouseevent.x, event.mouseevent.y)
                lastcount = len(xy[ind])
            firstgo = False
        event.canvas.draw()
    if show_ids:
        fig.canvas.mpl_connect('pick_event', show_label)
                                  

def export_figure(sc1, sc2, linepos, name, interp, file, size=(9,6), compress=False):
    make_figure(sc1, sc2, linepos, name, interp, size=size, compress=compress)
    plt.savefig(file)
        
def read_from_csv_oldformat(file):
    xs, ys, ids = [], [], []
    with open(file, 'r') as file:
        for _ in range(17):
            line = file.readline()
        while line != '':
            x, y, id, *_ = line.split(',')
            xs.append(x)
            ys.append(y)
            ids.append(id)
            line = file.readline()
    return xs, ys, ids


def read_from_csv(file):
    xs1, ys1, ids1 = [], [], []
    xs2, ys2, ids2 = [], [], []
    with open(file, 'r') as file:
        name, interp, opt = file.readline().strip().split(',')
        baseline_word, basetime = file.readline().strip().split(',')
        basetime = float(basetime)
        assert baseline_word == 'baseline'
        line = file.readline()
        while line != '':
            x1, y1, *rest = line.strip().split(',')
            xs1.append(int(x1))
            ys1.append(float(y1))
            if opt == 'BOTH':
                y2, *rest = rest
                xs2.append(int(x1))
                ys2.append(float(y2))
            id, = rest
            ids1.append(int(id))
            ids2.append(int(id))
            
            line = file.readline()
    if opt == 'BOTH':
        return (xs1, ys1, ids1), (xs2, ys2, ids2), basetime, name, interp
    elif opt == 'OPT':
        return (xs1, ys1, ids1), None, basetime, name, interp
    elif opt == 'NOOPT':
        return None, (xs1, ys1, ids1), basetime, name, interp
    
def summary(sc1, sc2, baseline):
    xs, ys1, ids = sc1
    _, ys2, _ = sc2
    data = zip(xs, ys1, ys2, ids)
    bl_opt_ratios = {}
    bl_noopt_ratios = {}
    opt_ratios = {}
    max_opt = [0,0,0]
    max_noopt = [0,0,0]
    for x, y1, y2, id in data:
        if y1/baseline > max_opt[0]:
            max_opt = y1/baseline, id, x
        if y2/baseline > max_noopt[0]:
            max_noopt = y2/baseline, id, x
        bl_opt_ratios[x,id] = (y1/baseline)
        bl_noopt_ratios[x,id] = (y2/baseline)
        opt_ratios[x,id] = (y1/y2)

    bl_opt_avg = sum(list(bl_opt_ratios.values()))/len(list(bl_opt_ratios.values()))
    bl_noopt_avg = sum(list(bl_noopt_ratios.values()))/len(list(bl_noopt_ratios.values()))
    opt_avg = sum(list(opt_ratios.values()))/len(list(opt_ratios.values()))

    bl_opt_full = [bl_opt_ratios[x,id] for x,id in bl_opt_ratios if x == 100]
    bl_opt_avg_full = sum(bl_opt_full)/len(bl_opt_full)
    bl_opt_none = [bl_opt_ratios[x,id] for x,id in bl_opt_ratios if x == 0]
    bl_opt_avg_none = sum(bl_opt_none)/len(bl_opt_none)

    bl_noopt_full = [bl_noopt_ratios[x,id] for x,id in bl_noopt_ratios if x == 100]
    bl_noopt_avg_full = sum(bl_noopt_full)/len(bl_noopt_full)
    bl_noopt_none = [bl_noopt_ratios[x,id] for x,id in bl_noopt_ratios if x == 0]
    bl_noopt_avg_none = sum(bl_noopt_none)/len(bl_noopt_none)

    opt_full = [opt_ratios[x,id] for x,id in opt_ratios if x == 100]
    opt_avg_full = sum(opt_full)/len(opt_full)
    opt_none = [opt_ratios[x,id] for x,id in opt_ratios if x == 0]
    opt_avg_none = sum(opt_none)/len(opt_none)
    
    print('''
Total, {} samples:
Average optimized overhead:        {:.3f}x
Average unoptimized overhead:      {:.3f}x
Ratio of optimized to unoptimized: {:.3f}x

At 100% typed, {} samples:
Average optimized overhead:        {:.3f}x
Average unoptimized overhead:      {:.3f}x
Ratio of optimized to unoptimized: {:.3f}x

At 0% typed, {} samples:
Average optimized overhead:        {:.3f}x
Average unoptimized overhead:      {:.3f}x
Ratio of optimized to unoptimized: {:.3f}x
'''.format(len(list(bl_opt_ratios.keys())), bl_opt_avg, bl_noopt_avg, opt_avg,
           len(bl_opt_full), bl_opt_avg_full, bl_noopt_avg_full, opt_avg_full,
           len(bl_opt_none), bl_opt_avg_none, bl_noopt_avg_none, opt_avg_none))
    print('''
Max optimized overhead:    {:.3f}x (sample {} at {}% typed)
Max unoptimized overhead:  {:.3f}x (sample {} at {}% typed)
'''.format(*(max_opt + max_noopt)))
    return {'samples':len(list(bl_opt_ratios.keys())), 
            'opt_overhead':bl_opt_avg, 
            'noopt_overhead':bl_noopt_avg, 
            'opt_noopt_overhead':opt_avg,
            'full_samples':len(bl_opt_full), 
            'full_opt_overhead': bl_opt_avg_full, 
            'full_noopt_overhead': bl_noopt_avg_full, 
            'full_opt_noopt_overhead': opt_avg_full,
            'un_samples':len(bl_opt_none), 
            'un_opt_overhead':bl_opt_avg_none, 
            'un_noopt_overhead':bl_noopt_avg_none, 
            'un_opt_noopt_overhead':opt_avg_none,
            'max_opt_overhead': max_opt[0],
            'max_noopt_overhead':max_noopt[0]
        }
        

    

if __name__ == '__main__':
    import argparse, sys
    parser = argparse.ArgumentParser(description='Generate graphs')
    parser.add_argument('--export', dest='export', action='store',
                        default=None, help='export as pdf')
    parser.add_argument('--old', dest='old', action='store_true',
                        default=False, help='use old format')
    parser.add_argument('--zoom', dest='zoom', action='store_true',
                        default=False, help='don\'t start at zero on the Y axis')
    parser.add_argument('csv', help='csv file containing data')

    args = parser.parse_args(sys.argv[1:])

    import matplotlib
    if args.export is not None:
        matplotlib.use('Agg')
    import matplotlib.pyplot as plt


    if args.old:
        sc1 = read_from_csv_oldformat(args.csv)
        sc2 = None
        basetime = 0
        import os.path
        try:
            name = args.csv.split(os.path.sep)[-2]
        except:
            name = '[unknown test case]'
        try:
            interp = os.path.basename(args.csv).split('.')[0].split('_')[1]
        except:
            interp = '[unknown interpreter]'
    else:
        sc1, sc2, basetime, name, interp = read_from_csv(args.csv)
        if sc2 is not None:
            summary(sc1, sc2, basetime)
    
    make_figure(sc1, sc2, basetime, name, interp, zoom=args.zoom, show_ids=(args.export is None))

    if args.export is None:
        plt.show()
    else:
        plt.savefig(args.export)
    
else:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
