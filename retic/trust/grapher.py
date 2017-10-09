FST_MARKER = 'o'
FST_COLOR = 'blue' # Blue
SND_MARKER = '^'
SND_COLOR = 'darkred' # Red
LINE_COLOR = 'black'

def make_figure(sc1, sc2, linepos, name, interp, *, zoom=False, show_ids=False):
    plt.figure()
    x1, y1, id1 = sc1
    line = plt.axhline(y=linepos, color=LINE_COLOR)
    l1 = plt.scatter(x1, y1, marker=FST_MARKER, c=FST_COLOR)
    if sc2 is not None:
        x2, y2, id2 = sc2
        l2 = plt.scatter(x2, y2, marker=SND_MARKER, c=SND_COLOR)
        plt.legend((line, l1, l2), ('Baseline performance', 'Optimized sample', 'Unoptimized sample'), scatterpoints=1, loc=2)
    else:
        plt.legend((line, l1), ('Baseline performance', 'Sample',), scatterpoints=1, loc=2)
    plt.xlabel('Percent of annotations given static types')
    plt.ylabel('Execution time (seconds)')
    plt.title('Execution times for {} under {}'.format(name, interp))
    plt.legend()
    axes = plt.gca()
    axes.set_xlim((0, 100))
    if not zoom:
        ymin, ymax = axes.get_ylim()
        axes.set_ylim((0, ymax+ymin/2))
    else:
        ymin = min(y1)
        ymax = max(y1)
        if sc2 is not None:
            ymin = min(ymin, *y2)
            ymax = max(ymax, *y2)
        dist = ymax - ymin
        axes.set_ylim((ymin-dist/5, ymax+dist/5))
                                  

def export_figure(sc1, sc2, linepos, name, interp, file):
    make_figure(sc1, sc2, linepos, name, interp)
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
    
    make_figure(sc1, sc2, basetime, name, interp, zoom=args.zoom)

    if args.export is None:
        plt.show()
    else:
        plt.savefig(args.export)
    
else:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
