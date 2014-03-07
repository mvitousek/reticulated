import pstat
import string, copy
from typed_math import *
__version__ = 0.6

def geometricmean(inlist: List(float)) ->float:
    mult = 1.0
    one_over_n = (1.0 / len(retic_cast(inlist, List(Float), Dyn, 'Argument of incorrect type in file stats.py')))
    for item in inlist:
        mult = (mult * pow(item, one_over_n))
    return mult

def harmonicmean(inlist: List(float)) ->float:
    sum = 0
    for item in inlist:
        sum = (sum + (1.0 / item))
    return (len(retic_cast(inlist, List(Float), Dyn, 'Argument of incorrect type in file stats.py')) / sum)

def mean(inlist: List(float)) ->float:
    sum = 0
    for item in inlist:
        sum = (sum + item)
    return (sum / float(retic_cast(len(retic_cast(inlist, List(Float), Dyn, 'Argument of incorrect type in file stats.py')), Int, Dyn, 'Argument of incorrect type in file stats.py')))

def median(inlist, numbins=retic_cast(1000, Int, Dyn, 'Default argument of incorrect type')) ->float:
    (hist, smallest, binsize, extras) = retic_cast(histogram(inlist, numbins, retic_cast([retic_cast(min, Dyn, Function(AnonymousParameters([Dyn]), Dyn), 'Function of incorrect type in file stats.py')(inlist), retic_cast(max, Dyn, Function(AnonymousParameters([Dyn]), Dyn), 'Function of incorrect type in file stats.py')(inlist)], List(Dyn), Dyn, 'Argument of incorrect type in file stats.py')), Tuple(List(Float), Float, Float, Int), Dyn, 'Assignee of incorrect type in file stats.py (line 290)')
    cumhist = cumsum(hist)
    for i in range(retic_cast(len(retic_cast(cumhist, List(Float), Dyn, 'Argument of incorrect type in file stats.py')), Int, Dyn, 'Argument of incorrect type in file stats.py')):
        if (cumhist[i] >= (len(inlist) / 2.0)):
            cfbin = i
            break
    LRL = (smallest + (binsize * cfbin))
    cfbelow = cumhist[(cfbin - 1)]
    freq = float(retic_cast(hist[cfbin], Float, Dyn, 'Argument of incorrect type in file stats.py'))
    _median = (LRL + ((((len(inlist) / 2.0) - cfbelow) / float(retic_cast(freq, Float, Dyn, 'Argument of incorrect type in file stats.py'))) * binsize))
    return _median

def medianscore(inlist: List(float)) ->float:
    newlist = retic_cast(retic_cast(copy, Dyn, Object('', {'deepcopy': Dyn, }), 'Attempting to access nonexistant attribute in file stats.py').deepcopy, Dyn, Function(AnonymousParameters([List(Float)]), Dyn), 'Function of incorrect type in file stats.py')(inlist)
    retic_cast(retic_cast(newlist, Dyn, Object('', {'sort': Dyn, }), 'Attempting to access nonexistant attribute in file stats.py').sort, Dyn, Function(AnonymousParameters([]), Dyn), 'Function of incorrect type in file stats.py')()
    if ((len(newlist) % 2) == 0):
        index = (len(newlist) / 2)
        median = retic_cast((float((newlist[index] + newlist[(index - 1)])) / 2), Float, Dyn, 'Assignee of incorrect type in file stats.py (line 315)')
    else:
        index = (len(newlist) / 2)
        median = newlist[index]
    return retic_cast(median, Dyn, Float, 'Return value of incorrect type')

def mode(inlist: List(float)) ->(int, List(float)):
    scores = pstat.unique(retic_cast(inlist, List(Float), List(Dyn), 'Argument of incorrect type in file stats.py'))
    retic_cast(scores.sort, Dyn, Function(AnonymousParameters([]), Dyn), 'Function of incorrect type in file stats.py')()
    freq = []
    for item in scores:
        freq.append(retic_cast(inlist.count, Dyn, Function(AnonymousParameters([Dyn]), Dyn), 'Function of incorrect type in file stats.py')(item))
    maxfreq = retic_cast(max, Dyn, Function(AnonymousParameters([List(Dyn)]), Dyn), 'Function of incorrect type in file stats.py')(freq)
    _mode = []
    stillmore = 1
    while stillmore:
        try:
            indx = freq.index(maxfreq)
            _mode.append(scores[indx])
            freq[indx]
            del freq[indx]
            scores[indx]
            del scores[indx]
        except ValueError:
            stillmore = 0
    return retic_cast((maxfreq, _mode), Tuple(Dyn, List(Dyn)), Tuple(Int, List(Float)), 'Return value of incorrect type')

def moment(inlist, moment=retic_cast(1, Int, Dyn, 'Default argument of incorrect type')) ->float:
    if (moment == 1):
        return 0.0
    else:
        mn = mean(retic_cast(inlist, Dyn, List(Float), 'Argument of incorrect type in file stats.py'))
        n = len(inlist)
        s = retic_cast(0, Int, Dyn, 'Assignee of incorrect type in file stats.py (line 368)')
        for x in inlist:
            s = (s + ((x - mn) ** moment))
        return retic_cast((s / float(retic_cast(n, Int, Dyn, 'Argument of incorrect type in file stats.py'))), Dyn, Float, 'Return value of incorrect type')

def variation(inlist: List(float)) ->float:
    return ((100.0 * samplestdev(inlist)) / float(retic_cast(mean(inlist), Float, Dyn, 'Argument of incorrect type in file stats.py')))

def skew(inlist: List(float)) ->float:
    return (moment(retic_cast(inlist, List(Float), Dyn, 'Argument of incorrect type in file stats.py'), retic_cast(3, Int, Dyn, 'Argument of incorrect type in file stats.py')) / pow(moment(retic_cast(inlist, List(Float), Dyn, 'Argument of incorrect type in file stats.py'), retic_cast(2, Int, Dyn, 'Argument of incorrect type in file stats.py')), 1.5))

def kurtosis(inlist: List(float)) ->float:
    return (moment(retic_cast(inlist, List(Float), Dyn, 'Argument of incorrect type in file stats.py'), retic_cast(4, Int, Dyn, 'Argument of incorrect type in file stats.py')) / pow(moment(retic_cast(inlist, List(Float), Dyn, 'Argument of incorrect type in file stats.py'), retic_cast(2, Int, Dyn, 'Argument of incorrect type in file stats.py')), 2.0))

def describe(inlist: List(float)) ->(int, (float, float), float, float, float, float):
    n = len(retic_cast(inlist, List(Float), Dyn, 'Argument of incorrect type in file stats.py'))
    mm = (retic_cast(min, Dyn, Function(AnonymousParameters([List(Float)]), Dyn), 'Function of incorrect type in file stats.py')(inlist), retic_cast(max, Dyn, Function(AnonymousParameters([List(Float)]), Dyn), 'Function of incorrect type in file stats.py')(inlist))
    m = mean(inlist)
    sd = stdev(inlist)
    sk = skew(inlist)
    kurt = kurtosis(inlist)
    return retic_cast((n, mm, m, sd, sk, kurt), Tuple(Int, Tuple(Dyn, Dyn), Float, Float, Float, Float), Tuple(Int, Tuple(Float, Float), Float, Float, Float, Float), 'Return value of incorrect type')

def itemfreq(inlist: List(float)) ->List((float, float)):
    scores = pstat.unique(retic_cast(inlist, List(Float), List(Dyn), 'Argument of incorrect type in file stats.py'))
    retic_cast(scores.sort, Dyn, Function(AnonymousParameters([]), Dyn), 'Function of incorrect type in file stats.py')()
    freq = []
    for item in scores:
        freq.append(retic_cast(inlist.count, Dyn, Function(AnonymousParameters([Dyn]), Dyn), 'Function of incorrect type in file stats.py')(item))
    return retic_cast(pstat.abut(retic_cast(scores, List(Dyn), Dyn, 'Argument of incorrect type in file stats.py'), retic_cast(freq, List(Dyn), Dyn, 'Argument of incorrect type in file stats.py')), List(Dyn), List(Tuple(Float, Float)), 'Return value of incorrect type')

def scoreatpercentile(inlist: List(float), percent: float) ->float:
    if (percent > 1):
        retic_cast(print, Dyn, Function(AnonymousParameters([String]), Dyn), 'Function of incorrect type in file stats.py')('\nDividing percent>1 by 100 in lscoreatpercentile().\n')
        percent = (percent / 100.0)
    targetcf = (percent * len(retic_cast(inlist, List(Float), Dyn, 'Argument of incorrect type in file stats.py')))
    (h, lrl, binsize, extras) = retic_cast(histogram(retic_cast(inlist, List(Float), Dyn, 'Argument of incorrect type in file stats.py')), Tuple(List(Float), Float, Float, Int), Dyn, 'Assignee of incorrect type in file stats.py (line 451)')
    cumhist = cumsum(retic_cast(retic_cast(retic_cast(copy, Dyn, Object('', {'deepcopy': Dyn, }), 'Attempting to access nonexistant attribute in file stats.py').deepcopy, Dyn, Function(AnonymousParameters([List(Float)]), Dyn), 'Function of incorrect type in file stats.py')(h), Dyn, List(Float), 'Argument of incorrect type in file stats.py'))
    for i in range(retic_cast(len(retic_cast(cumhist, List(Float), Dyn, 'Argument of incorrect type in file stats.py')), Int, Dyn, 'Argument of incorrect type in file stats.py')):
        if (cumhist[i] >= targetcf):
            break
    score = ((binsize * ((targetcf - cumhist[(i - 1)]) / float(retic_cast(h[i], Float, Dyn, 'Argument of incorrect type in file stats.py')))) + (lrl + (binsize * i)))
    return score

def percentileofscore(inlist, score, histbins=retic_cast(10, Int, Dyn, 'Default argument of incorrect type'), defaultlimits=None) ->float:
    (h, lrl, binsize, extras) = retic_cast(histogram(inlist, histbins, defaultlimits), Tuple(List(Float), Float, Float, Int), Dyn, 'Assignee of incorrect type in file stats.py (line 468)')
    cumhist = cumsum(retic_cast(retic_cast(retic_cast(copy, Dyn, Object('', {'deepcopy': Dyn, }), 'Attempting to access nonexistant attribute in file stats.py').deepcopy, Dyn, Function(AnonymousParameters([List(Float)]), Dyn), 'Function of incorrect type in file stats.py')(h), Dyn, List(Float), 'Argument of incorrect type in file stats.py'))
    i = int(((score - lrl) / float(retic_cast(binsize, Float, Dyn, 'Argument of incorrect type in file stats.py'))))
    pct = (((cumhist[(i - 1)] + (((score - (lrl + (binsize * i))) / float(retic_cast(binsize, Float, Dyn, 'Argument of incorrect type in file stats.py'))) * h[i])) / float(retic_cast(len(inlist), Int, Dyn, 'Argument of incorrect type in file stats.py'))) * 100)
    return retic_cast(pct, Dyn, Float, 'Return value of incorrect type')

def histogram(inlist, numbins=retic_cast(10, Int, Dyn, 'Default argument of incorrect type'), defaultreallimits=None, printextras=retic_cast(0, Int, Dyn, 'Default argument of incorrect type')) ->(List(float), float, float, int):
    if (defaultreallimits != None):
        if ((retic_cast(type, Dyn, Function(AnonymousParameters([Dyn]), Dyn), 'Function of incorrect type in file stats.py')(defaultreallimits) not in [list, tuple]) or (len(defaultreallimits) == 1)):
            lowerreallimit = defaultreallimits
            upperreallimit = (1.000001 * retic_cast(max, Dyn, Function(AnonymousParameters([Dyn]), Dyn), 'Function of incorrect type in file stats.py')(inlist))
        else:
            lowerreallimit = defaultreallimits[0]
            upperreallimit = defaultreallimits[1]
        binsize = ((upperreallimit - lowerreallimit) / float(numbins))
    else:
        estbinwidth = (((retic_cast(max, Dyn, Function(AnonymousParameters([Dyn]), Dyn), 'Function of incorrect type in file stats.py')(inlist) - retic_cast(min, Dyn, Function(AnonymousParameters([Dyn]), Dyn), 'Function of incorrect type in file stats.py')(inlist)) / float(numbins)) + 1e-06)
        binsize = (((retic_cast(max, Dyn, Function(AnonymousParameters([Dyn]), Dyn), 'Function of incorrect type in file stats.py')(inlist) - retic_cast(min, Dyn, Function(AnonymousParameters([Dyn]), Dyn), 'Function of incorrect type in file stats.py')(inlist)) + estbinwidth) / float(numbins))
        lowerreallimit = (retic_cast(min, Dyn, Function(AnonymousParameters([Dyn]), Dyn), 'Function of incorrect type in file stats.py')(inlist) - (binsize / 2))
    bins = ([0] * numbins)
    extrapoints = 0
    for num in inlist:
        try:
            if ((num - lowerreallimit) < 0):
                extrapoints = (extrapoints + 1)
            else:
                bintoincrement = int(((num - lowerreallimit) / float(binsize)))
                bins[bintoincrement] = (bins[bintoincrement] + 1)
        except:
            extrapoints = (extrapoints + 1)
    if ((extrapoints > 0) and (printextras == 1)):
        retic_cast(print, Dyn, Function(AnonymousParameters([String, Int]), Dyn), 'Function of incorrect type in file stats.py')('\nPoints outside given histogram range =', extrapoints)
    return retic_cast((bins, lowerreallimit, binsize, extrapoints), Tuple(Dyn, Dyn, Dyn, Int), Tuple(List(Float), Float, Float, Int), 'Return value of incorrect type')

def cumfreq(inlist, numbins=retic_cast(10, Int, Dyn, 'Default argument of incorrect type'), defaultreallimits=None) ->(List(float), float, float, int):
    (h, l, b, e) = retic_cast(histogram(inlist, numbins, defaultreallimits), Tuple(List(Float), Float, Float, Int), Dyn, 'Assignee of incorrect type in file stats.py (line 521)')
    cumhist = cumsum(retic_cast(retic_cast(retic_cast(copy, Dyn, Object('', {'deepcopy': Dyn, }), 'Attempting to access nonexistant attribute in file stats.py').deepcopy, Dyn, Function(AnonymousParameters([List(Float)]), Dyn), 'Function of incorrect type in file stats.py')(h), Dyn, List(Float), 'Argument of incorrect type in file stats.py'))
    return (cumhist, l, b, e)

def relfreq(inlist, numbins=retic_cast(10, Int, Dyn, 'Default argument of incorrect type'), defaultreallimits=None) ->(List(float), float, float, int):
    (h, l, b, e) = retic_cast(histogram(inlist, numbins, defaultreallimits), Tuple(List(Float), Float, Float, Int), Dyn, 'Assignee of incorrect type in file stats.py (line 533)')
    for i in range(retic_cast(len(retic_cast(h, List(Float), Dyn, 'Argument of incorrect type in file stats.py')), Int, Dyn, 'Argument of incorrect type in file stats.py')):
        h[i] = (h[i] / float(retic_cast(len(inlist), Int, Dyn, 'Argument of incorrect type in file stats.py')))
    return (h, l, b, e)

def obrientransform(*args) ->List(List(float)):
    TINY = 1e-10
    k = len(args)
    n = ([0.0] * k)
    v = ([0.0] * k)
    m = ([0.0] * k)
    nargs = []
    for i in range(retic_cast(k, Int, Dyn, 'Argument of incorrect type in file stats.py')):
        nargs.append(retic_cast(retic_cast(copy, Dyn, Object('', {'deepcopy': Dyn, }), 'Attempting to access nonexistant attribute in file stats.py').deepcopy, Dyn, Function(AnonymousParameters([Dyn]), Dyn), 'Function of incorrect type in file stats.py')(args[i]))
        n[i] = float(retic_cast(len(nargs[i]), Int, Dyn, 'Argument of incorrect type in file stats.py'))
        v[i] = var(retic_cast(nargs[i], Dyn, List(Float), 'Argument of incorrect type in file stats.py'))
        m[i] = mean(retic_cast(nargs[i], Dyn, List(Float), 'Argument of incorrect type in file stats.py'))
    for j in range(retic_cast(k, Int, Dyn, 'Argument of incorrect type in file stats.py')):
        for i in range(retic_cast(n[j], Float, Dyn, 'Argument of incorrect type in file stats.py')):
            t1 = (((n[j] - 1.5) * n[j]) * ((nargs[j][i] - m[j]) ** 2))
            t2 = ((0.5 * v[j]) * (n[j] - 1.0))
            t3 = ((n[j] - 1.0) * (n[j] - 2.0))
            nargs[j][i] = ((t1 - t2) / float(retic_cast(t3, Float, Dyn, 'Argument of incorrect type in file stats.py')))
    check = 1
    for j in range(retic_cast(k, Int, Dyn, 'Argument of incorrect type in file stats.py')):
        if ((v[j] - mean(retic_cast(nargs[j], Dyn, List(Float), 'Argument of incorrect type in file stats.py'))) > TINY):
            check = 0
    if (check != 1):
        raise retic_cast(ValueError, Dyn, Function(AnonymousParameters([String]), Dyn), 'Function of incorrect type in file stats.py')('Problem in obrientransform.')
    else:
        return retic_cast(nargs, List(Dyn), List(List(Float)), 'Return value of incorrect type')

def samplevar(inlist: List(float)) ->float:
    n = len(retic_cast(inlist, List(Float), Dyn, 'Argument of incorrect type in file stats.py'))
    mn = mean(inlist)
    deviations = []
    for item in inlist:
        deviations.append(retic_cast((item - mn), Float, Dyn, 'Argument of incorrect type in file stats.py'))
    return (ss(retic_cast(deviations, List(Dyn), List(Float), 'Argument of incorrect type in file stats.py')) / float(retic_cast(n, Int, Dyn, 'Argument of incorrect type in file stats.py')))

def samplestdev(inlist: List(float)) ->float:
    return sqrt(samplevar(inlist))

def cov(x, y, keepdims=retic_cast(0, Int, Dyn, 'Default argument of incorrect type')) ->float:
    n = len(x)
    xmn = mean(retic_cast(x, Dyn, List(Float), 'Argument of incorrect type in file stats.py'))
    ymn = mean(retic_cast(y, Dyn, List(Float), 'Argument of incorrect type in file stats.py'))
    xdeviations = ([0] * len(x))
    ydeviations = ([0] * len(y))
    for i in range(retic_cast(len(x), Int, Dyn, 'Argument of incorrect type in file stats.py')):
        xdeviations[i] = retic_cast((x[i] - xmn), Dyn, Int, 'Assignee of incorrect type in file stats.py (line 621)')
        ydeviations[i] = retic_cast((y[i] - ymn), Dyn, Int, 'Assignee of incorrect type in file stats.py (line 622)')
    ss = 0.0
    for i in range(retic_cast(len(retic_cast(xdeviations, List(Int), Dyn, 'Argument of incorrect type in file stats.py')), Int, Dyn, 'Argument of incorrect type in file stats.py')):
        ss = (ss + (xdeviations[i] * ydeviations[i]))
    return (ss / float(retic_cast((n - 1), Int, Dyn, 'Argument of incorrect type in file stats.py')))

def var(inlist: List(float)) ->float:
    n = len(retic_cast(inlist, List(Float), Dyn, 'Argument of incorrect type in file stats.py'))
    mn = mean(inlist)
    deviations = dyn(retic_cast(([0] * len(retic_cast(inlist, List(Float), Dyn, 'Argument of incorrect type in file stats.py'))), List(Int), Dyn, 'Argument of incorrect type in file stats.py'))
    for i in range(retic_cast(len(retic_cast(inlist, List(Float), Dyn, 'Argument of incorrect type in file stats.py')), Int, Dyn, 'Argument of incorrect type in file stats.py')):
        deviations[i] = retic_cast((inlist[i] - mn), Float, Dyn, 'Assignee of incorrect type in file stats.py (line 640)')
    return (ss(retic_cast(deviations, Dyn, List(Float), 'Argument of incorrect type in file stats.py')) / float(retic_cast((n - 1), Int, Dyn, 'Argument of incorrect type in file stats.py')))

def stdev(inlist: List(float)) ->float:
    return sqrt(var(inlist))

def sterr(inlist: List(float)) ->float:
    return (stdev(inlist) / float(retic_cast(sqrt(len(retic_cast(inlist, List(Float), Dyn, 'Argument of incorrect type in file stats.py'))), Float, Dyn, 'Argument of incorrect type in file stats.py')))

def sem(inlist: List(float)) ->float:
    sd = stdev(inlist)
    n = len(retic_cast(inlist, List(Float), Dyn, 'Argument of incorrect type in file stats.py'))
    return (sd / sqrt(n))

def z(inlist: List(float), score: float) ->float:
    _z = ((score - mean(inlist)) / samplestdev(inlist))
    return _z

def zs(inlist: List(float)) ->List(float):
    zscores = []
    for item in inlist:
        zscores.append(retic_cast(z(inlist, item), Float, Dyn, 'Argument of incorrect type in file stats.py'))
    return retic_cast(zscores, List(Dyn), List(Float), 'Return value of incorrect type')

def trimboth(l: List(Dyn), proportiontocut: float) ->List(Dyn):
    lowercut = int(retic_cast((proportiontocut * len(retic_cast(l, List(Dyn), Dyn, 'Argument of incorrect type in file stats.py'))), Float, Dyn, 'Argument of incorrect type in file stats.py'))
    uppercut = (len(retic_cast(l, List(Dyn), Dyn, 'Argument of incorrect type in file stats.py')) - lowercut)
    return l[lowercut:uppercut]

def trim1(l, proportiontocut, tail=retic_cast('right', String, Dyn, 'Default argument of incorrect type')) ->List(Dyn):
    if (tail == 'right'):
        lowercut = 0
        uppercut = (len(l) - int((proportiontocut * len(l))))
    elif (tail == 'left'):
        lowercut = int((proportiontocut * len(l)))
        uppercut = len(l)
    return retic_cast(l[lowercut:uppercut], Dyn, List(Dyn), 'Return value of incorrect type')

def paired(x, y):
    samples = retic_cast('', String, Dyn, 'Assignee of incorrect type in file stats.py (line 750)')
    while (samples not in ['i', 'r', 'I', 'R', 'c', 'C']):
        retic_cast(print, Dyn, Function(DynParameters, Dyn), 'Function of incorrect type in file stats.py')('\nIndependent or related samples, or correlation (i,r,c): ', end=' ')
        samples = retic_cast(input, Dyn, Function(AnonymousParameters([]), Dyn), 'Function of incorrect type in file stats.py')()
    if (samples in ['i', 'I', 'r', 'R']):
        retic_cast(print, Dyn, Function(DynParameters, Dyn), 'Function of incorrect type in file stats.py')('\nComparing variances ...', end=' ')
        r = retic_cast(obrientransform(x, y), List(List(Float)), Dyn, 'Assignee of incorrect type in file stats.py (line 758)')
        (f, p) = retic_cast(F_oneway(pstat.colex(retic_cast(r, Dyn, List(List(Dyn)), 'Argument of incorrect type in file stats.py'), retic_cast(0, Int, Dyn, 'Argument of incorrect type in file stats.py')), pstat.colex(retic_cast(r, Dyn, List(List(Dyn)), 'Argument of incorrect type in file stats.py'), retic_cast(1, Int, Dyn, 'Argument of incorrect type in file stats.py'))), Tuple(Float, Float), Dyn, 'Assignee of incorrect type in file stats.py (line 759)')
        if (p < 0.05):
            vartype = ('unequal, p=' + str(retic_cast(round(retic_cast(p, Float, Dyn, 'Argument of incorrect type in file stats.py'), retic_cast(4, Int, Dyn, 'Argument of incorrect type in file stats.py')), Float, Dyn, 'Argument of incorrect type in file stats.py')))
        else:
            vartype = 'equal'
        retic_cast(print, Dyn, Function(AnonymousParameters([String]), Dyn), 'Function of incorrect type in file stats.py')(vartype)
        if (samples in ['i', 'I']):
            if (vartype[0] == 'e'):
                (t, p) = retic_cast(ttest_ind(x, y, retic_cast(0, Int, Dyn, 'Argument of incorrect type in file stats.py')), Tuple(Float, Float), Dyn, 'Assignee of incorrect type in file stats.py (line 767)')
                retic_cast(print, Dyn, Function(AnonymousParameters([String, Float, Float]), Dyn), 'Function of incorrect type in file stats.py')('\nIndependent samples t-test:  ', round(retic_cast(t, Float, Dyn, 'Argument of incorrect type in file stats.py'), retic_cast(4, Int, Dyn, 'Argument of incorrect type in file stats.py')), round(retic_cast(p, Float, Dyn, 'Argument of incorrect type in file stats.py'), retic_cast(4, Int, Dyn, 'Argument of incorrect type in file stats.py')))
            elif ((len(x) > 20) or (len(y) > 20)):
                (z, p) = retic_cast(ranksums(retic_cast(x, Dyn, List(Float), 'Argument of incorrect type in file stats.py'), retic_cast(y, Dyn, List(Float), 'Argument of incorrect type in file stats.py')), Tuple(Float, Float), Dyn, 'Assignee of incorrect type in file stats.py (line 771)')
                retic_cast(print, Dyn, Function(AnonymousParameters([String, Float, Float]), Dyn), 'Function of incorrect type in file stats.py')('\nRank Sums test (NONparametric, n>20):  ', round(retic_cast(z, Float, Dyn, 'Argument of incorrect type in file stats.py'), retic_cast(4, Int, Dyn, 'Argument of incorrect type in file stats.py')), round(retic_cast(p, Float, Dyn, 'Argument of incorrect type in file stats.py'), retic_cast(4, Int, Dyn, 'Argument of incorrect type in file stats.py')))
            else:
                (u, p) = retic_cast(mannwhitneyu(retic_cast(x, Dyn, List(Float), 'Argument of incorrect type in file stats.py'), retic_cast(y, Dyn, List(Float), 'Argument of incorrect type in file stats.py')), Tuple(Float, Float), Dyn, 'Assignee of incorrect type in file stats.py (line 774)')
                retic_cast(print, Dyn, Function(AnonymousParameters([String, Float, Float]), Dyn), 'Function of incorrect type in file stats.py')('\nMann-Whitney U-test (NONparametric, ns<20):  ', round(retic_cast(u, Float, Dyn, 'Argument of incorrect type in file stats.py'), retic_cast(4, Int, Dyn, 'Argument of incorrect type in file stats.py')), round(retic_cast(p, Float, Dyn, 'Argument of incorrect type in file stats.py'), retic_cast(4, Int, Dyn, 'Argument of incorrect type in file stats.py')))
        elif (vartype[0] == 'e'):
            (t, p) = retic_cast(ttest_rel(x, y, retic_cast(0, Int, Dyn, 'Argument of incorrect type in file stats.py')), Tuple(Float, Float), Dyn, 'Assignee of incorrect type in file stats.py (line 779)')
            retic_cast(print, Dyn, Function(AnonymousParameters([String, Float, Float]), Dyn), 'Function of incorrect type in file stats.py')('\nRelated samples t-test:  ', round(retic_cast(t, Float, Dyn, 'Argument of incorrect type in file stats.py'), retic_cast(4, Int, Dyn, 'Argument of incorrect type in file stats.py')), round(retic_cast(p, Float, Dyn, 'Argument of incorrect type in file stats.py'), retic_cast(4, Int, Dyn, 'Argument of incorrect type in file stats.py')))
        else:
            (t, p) = retic_cast(ranksums(retic_cast(x, Dyn, List(Float), 'Argument of incorrect type in file stats.py'), retic_cast(y, Dyn, List(Float), 'Argument of incorrect type in file stats.py')), Tuple(Float, Float), Dyn, 'Assignee of incorrect type in file stats.py (line 782)')
            retic_cast(print, Dyn, Function(AnonymousParameters([String, Float, Float]), Dyn), 'Function of incorrect type in file stats.py')('\nWilcoxon T-test (NONparametric):  ', round(retic_cast(t, Float, Dyn, 'Argument of incorrect type in file stats.py'), retic_cast(4, Int, Dyn, 'Argument of incorrect type in file stats.py')), round(retic_cast(p, Float, Dyn, 'Argument of incorrect type in file stats.py'), retic_cast(4, Int, Dyn, 'Argument of incorrect type in file stats.py')))
    else:
        corrtype = retic_cast('', String, Dyn, 'Assignee of incorrect type in file stats.py (line 785)')
        while (corrtype not in ['c', 'C', 'r', 'R', 'd', 'D']):
            retic_cast(print, Dyn, Function(DynParameters, Dyn), 'Function of incorrect type in file stats.py')('\nIs the data Continuous, Ranked, or Dichotomous (c,r,d): ', end=' ')
            corrtype = retic_cast(input, Dyn, Function(AnonymousParameters([]), Dyn), 'Function of incorrect type in file stats.py')()
        if (corrtype in ['c', 'C']):
            (m, b, r, p, see) = retic_cast(linregress(retic_cast(x, Dyn, List(Float), 'Argument of incorrect type in file stats.py'), retic_cast(y, Dyn, List(Float), 'Argument of incorrect type in file stats.py')), Tuple(Float, Float, Float, Float, Float), Dyn, 'Assignee of incorrect type in file stats.py (line 790)')
            retic_cast(print, Dyn, Function(AnonymousParameters([String]), Dyn), 'Function of incorrect type in file stats.py')('\nLinear regression for continuous variables ...')
            lol = [['Slope', 'Intercept', 'r', 'Prob', 'SEestimate'], [round(retic_cast(m, Float, Dyn, 'Argument of incorrect type in file stats.py'), retic_cast(4, Int, Dyn, 'Argument of incorrect type in file stats.py')), round(retic_cast(b, Float, Dyn, 'Argument of incorrect type in file stats.py'), retic_cast(4, Int, Dyn, 'Argument of incorrect type in file stats.py')), round(r, retic_cast(4, Int, Dyn, 'Argument of incorrect type in file stats.py')), round(retic_cast(p, Float, Dyn, 'Argument of incorrect type in file stats.py'), retic_cast(4, Int, Dyn, 'Argument of incorrect type in file stats.py')), round(retic_cast(see, Float, Dyn, 'Argument of incorrect type in file stats.py'), retic_cast(4, Int, Dyn, 'Argument of incorrect type in file stats.py'))]]
            pstat.printcc(retic_cast(lol, List(List(Dyn)), Dyn, 'Argument of incorrect type in file stats.py'))
        elif (corrtype in ['r', 'R']):
            (r, p) = retic_cast(spearmanr(retic_cast(x, Dyn, List(Float), 'Argument of incorrect type in file stats.py'), retic_cast(y, Dyn, List(Float), 'Argument of incorrect type in file stats.py')), Tuple(Float, Float), Dyn, 'Assignee of incorrect type in file stats.py (line 795)')
            retic_cast(print, Dyn, Function(AnonymousParameters([String]), Dyn), 'Function of incorrect type in file stats.py')('\nCorrelation for ranked variables ...')
            retic_cast(print, Dyn, Function(AnonymousParameters([String, Float, Float]), Dyn), 'Function of incorrect type in file stats.py')("Spearman's r: ", round(r, retic_cast(4, Int, Dyn, 'Argument of incorrect type in file stats.py')), round(retic_cast(p, Float, Dyn, 'Argument of incorrect type in file stats.py'), retic_cast(4, Int, Dyn, 'Argument of incorrect type in file stats.py')))
        else:
            (r, p) = retic_cast(pointbiserialr(retic_cast(x, Dyn, List(Float), 'Argument of incorrect type in file stats.py'), retic_cast(y, Dyn, List(Float), 'Argument of incorrect type in file stats.py')), Tuple(Float, Float), Dyn, 'Assignee of incorrect type in file stats.py (line 799)')
            retic_cast(print, Dyn, Function(AnonymousParameters([String]), Dyn), 'Function of incorrect type in file stats.py')('\nAssuming x contains a dichotomous variable ...')
            retic_cast(print, Dyn, Function(AnonymousParameters([String, Float, Float]), Dyn), 'Function of incorrect type in file stats.py')('Point Biserial r: ', round(r, retic_cast(4, Int, Dyn, 'Argument of incorrect type in file stats.py')), round(retic_cast(p, Float, Dyn, 'Argument of incorrect type in file stats.py'), retic_cast(4, Int, Dyn, 'Argument of incorrect type in file stats.py')))
    retic_cast(print, Dyn, Function(AnonymousParameters([String]), Dyn), 'Function of incorrect type in file stats.py')('\n\n')
    return None

def pearsonr(x: List(float), y: List(float)) ->(float, float):
    TINY = 1e-30
    if (len(retic_cast(x, List(Float), Dyn, 'Argument of incorrect type in file stats.py')) != len(retic_cast(y, List(Float), Dyn, 'Argument of incorrect type in file stats.py'))):
        raise retic_cast(ValueError, Dyn, Function(AnonymousParameters([String]), Dyn), 'Function of incorrect type in file stats.py')('Input values not paired in pearsonr.  Aborting.')
    n = len(retic_cast(x, List(Float), Dyn, 'Argument of incorrect type in file stats.py'))
    x = retic_cast(list(retic_cast(map, Dyn, Function(AnonymousParameters([Function(DynParameters, Float), List(Float)]), Dyn), 'Function of incorrect type in file stats.py')(float, x)), List(Dyn), List(Float), 'Assignee of incorrect type in file stats.py (line 819)')
    y = retic_cast(list(retic_cast(map, Dyn, Function(AnonymousParameters([Function(DynParameters, Float), List(Float)]), Dyn), 'Function of incorrect type in file stats.py')(float, y)), List(Dyn), List(Float), 'Assignee of incorrect type in file stats.py (line 820)')
    xmean = mean(x)
    ymean = mean(y)
    r_num = ((n * summult(x, y)) - (sum(x) * sum(y)))
    r_den = sqrt((((n * ss(x)) - square_of_sums(x)) * ((n * ss(y)) - square_of_sums(y))))
    r = (r_num / r_den)
    df = (n - 2)
    t = (r * sqrt((df / (((1.0 - r) + TINY) * ((1.0 + r) + TINY)))))
    prob = betai((0.5 * df), 0.5, (df / float(retic_cast((df + (t * t)), Float, Dyn, 'Argument of incorrect type in file stats.py'))))
    return (r, prob)

def lincc(x: float, y: float) ->float:
    covar = ((retic_cast(lcov, Dyn, Function(AnonymousParameters([Float, Float]), Dyn), 'Function of incorrect type in file stats.py')(x, y) * (len(retic_cast(x, Float, Dyn, 'Argument of incorrect type in file stats.py')) - 1)) / float(retic_cast(len(retic_cast(x, Float, Dyn, 'Argument of incorrect type in file stats.py')), Int, Dyn, 'Argument of incorrect type in file stats.py')))
    xvar = ((retic_cast(lvar, Dyn, Function(AnonymousParameters([Float]), Dyn), 'Function of incorrect type in file stats.py')(x) * (len(retic_cast(x, Float, Dyn, 'Argument of incorrect type in file stats.py')) - 1)) / float(retic_cast(len(retic_cast(x, Float, Dyn, 'Argument of incorrect type in file stats.py')), Int, Dyn, 'Argument of incorrect type in file stats.py')))
    yvar = ((retic_cast(lvar, Dyn, Function(AnonymousParameters([Float]), Dyn), 'Function of incorrect type in file stats.py')(y) * (len(retic_cast(y, Float, Dyn, 'Argument of incorrect type in file stats.py')) - 1)) / float(retic_cast(len(retic_cast(y, Float, Dyn, 'Argument of incorrect type in file stats.py')), Int, Dyn, 'Argument of incorrect type in file stats.py')))
    _lincc = ((2 * covar) / ((xvar + yvar) + ((retic_cast(amean, Dyn, Function(AnonymousParameters([Float]), Dyn), 'Function of incorrect type in file stats.py')(x) - retic_cast(amean, Dyn, Function(AnonymousParameters([Float]), Dyn), 'Function of incorrect type in file stats.py')(y)) ** 2)))
    return retic_cast(_lincc, Dyn, Float, 'Return value of incorrect type')

def spearmanr(x: List(float), y: List(float)) ->(float, float):
    TINY = 1e-30
    if (len(retic_cast(x, List(Float), Dyn, 'Argument of incorrect type in file stats.py')) != len(retic_cast(y, List(Float), Dyn, 'Argument of incorrect type in file stats.py'))):
        raise retic_cast(ValueError, Dyn, Function(AnonymousParameters([String]), Dyn), 'Function of incorrect type in file stats.py')('Input values not paired in spearmanr.  Aborting.')
    n = len(retic_cast(x, List(Float), Dyn, 'Argument of incorrect type in file stats.py'))
    rankx = rankdata(x)
    ranky = rankdata(y)
    dsq = sumdiffsquared(rankx, ranky)
    rs = (1 - ((6 * dsq) / float(retic_cast((n * ((n ** 2) - 1)), Int, Dyn, 'Argument of incorrect type in file stats.py'))))
    t = (rs * sqrt(((n - 2) / ((rs + 1.0) * (1.0 - rs)))))
    df = (n - 2)
    probrs = betai((0.5 * df), 0.5, (df / (df + (t * t))))
    return (rs, probrs)

def pointbiserialr(x: List(float), y: List(float)) ->(float, float):
    TINY = 1e-30
    if (len(retic_cast(x, List(Float), Dyn, 'Argument of incorrect type in file stats.py')) != len(retic_cast(y, List(Float), Dyn, 'Argument of incorrect type in file stats.py'))):
        raise retic_cast(ValueError, Dyn, Function(AnonymousParameters([String]), Dyn), 'Function of incorrect type in file stats.py')('INPUT VALUES NOT PAIRED IN pointbiserialr.  ABORTING.')
    data = pstat.abut(retic_cast(x, List(Float), Dyn, 'Argument of incorrect type in file stats.py'), retic_cast(y, List(Float), Dyn, 'Argument of incorrect type in file stats.py'))
    categories = pstat.unique(retic_cast(x, List(Float), List(Dyn), 'Argument of incorrect type in file stats.py'))
    if (len(retic_cast(categories, List(Dyn), Dyn, 'Argument of incorrect type in file stats.py')) != 2):
        raise retic_cast(ValueError, Dyn, Function(AnonymousParameters([String]), Dyn), 'Function of incorrect type in file stats.py')('Exactly 2 categories required for pointbiserialr().')
    else:
        codemap = pstat.abut(retic_cast(categories, List(Dyn), Dyn, 'Argument of incorrect type in file stats.py'), retic_cast(list(retic_cast(range(retic_cast(2, Int, Dyn, 'Argument of incorrect type in file stats.py')), List(Int), Dyn, 'Argument of incorrect type in file stats.py')), List(Dyn), Dyn, 'Argument of incorrect type in file stats.py'))
        recoded = pstat.recode(retic_cast(data, List(Dyn), Dyn, 'Argument of incorrect type in file stats.py'), retic_cast(codemap, List(Dyn), Dyn, 'Argument of incorrect type in file stats.py'), retic_cast(0, Int, Dyn, 'Argument of incorrect type in file stats.py'))
        _x = pstat.linexand(retic_cast(data, List(Dyn), List(List(Dyn)), 'Argument of incorrect type in file stats.py'), retic_cast(0, Int, Dyn, 'Argument of incorrect type in file stats.py'), categories[0])
        _y = pstat.linexand(retic_cast(data, List(Dyn), List(List(Dyn)), 'Argument of incorrect type in file stats.py'), retic_cast(0, Int, Dyn, 'Argument of incorrect type in file stats.py'), categories[1])
        xmean = mean(retic_cast(pstat.colex(_x, retic_cast(1, Int, Dyn, 'Argument of incorrect type in file stats.py')), Dyn, List(Float), 'Argument of incorrect type in file stats.py'))
        ymean = mean(retic_cast(pstat.colex(_y, retic_cast(1, Int, Dyn, 'Argument of incorrect type in file stats.py')), Dyn, List(Float), 'Argument of incorrect type in file stats.py'))
        n = len(retic_cast(data, List(Dyn), Dyn, 'Argument of incorrect type in file stats.py'))
        adjust = sqrt(((len(retic_cast(_x, List(List(Dyn)), Dyn, 'Argument of incorrect type in file stats.py')) / float(retic_cast(n, Int, Dyn, 'Argument of incorrect type in file stats.py'))) * (len(retic_cast(_y, List(List(Dyn)), Dyn, 'Argument of incorrect type in file stats.py')) / float(retic_cast(n, Int, Dyn, 'Argument of incorrect type in file stats.py')))))
        rpb = (((ymean - xmean) / samplestdev(retic_cast(pstat.colex(retic_cast(data, List(Dyn), List(List(Dyn)), 'Argument of incorrect type in file stats.py'), retic_cast(1, Int, Dyn, 'Argument of incorrect type in file stats.py')), Dyn, List(Float), 'Argument of incorrect type in file stats.py'))) * adjust)
        df = (n - 2)
        t = (rpb * sqrt((df / (((1.0 - rpb) + TINY) * ((1.0 + rpb) + TINY)))))
        prob = betai((0.5 * df), 0.5, (df / (df + (t * t))))
        return (rpb, prob)

def kendalltau(x: List(float), y: List(float)) ->(float, float):
    n1 = 0
    n2 = 0
    iss = 0
    for j in range(retic_cast((len(retic_cast(x, List(Float), Dyn, 'Argument of incorrect type in file stats.py')) - 1), Int, Dyn, 'Argument of incorrect type in file stats.py')):
        for k in range(retic_cast(j, Int, Dyn, 'Argument of incorrect type in file stats.py'), retic_cast(len(retic_cast(y, List(Float), Dyn, 'Argument of incorrect type in file stats.py')), Int, Dyn, 'Argument of incorrect type in file stats.py')):
            a1 = (x[j] - x[k])
            a2 = (y[j] - y[k])
            aa = (a1 * a2)
            if aa:
                n1 = (n1 + 1)
                n2 = (n2 + 1)
                if (aa > 0):
                    iss = (iss + 1)
                else:
                    iss = (iss - 1)
            elif a1:
                n1 = (n1 + 1)
            else:
                n2 = (n2 + 1)
    tau = (iss / sqrt((n1 * n2)))
    svar = (((4.0 * len(retic_cast(x, List(Float), Dyn, 'Argument of incorrect type in file stats.py'))) + 10.0) / ((9.0 * len(retic_cast(x, List(Float), Dyn, 'Argument of incorrect type in file stats.py'))) * (len(retic_cast(x, List(Float), Dyn, 'Argument of incorrect type in file stats.py')) - 1)))
    z = (tau / sqrt(svar))
    prob = erfcc((abs(z) / 1.4142136))
    return (tau, prob)

def linregress(x: List(float), y: List(float)) ->(float, float, float, float, float):
    TINY = 1e-20
    if (len(retic_cast(x, List(Float), Dyn, 'Argument of incorrect type in file stats.py')) != len(retic_cast(y, List(Float), Dyn, 'Argument of incorrect type in file stats.py'))):
        raise retic_cast(ValueError, Dyn, Function(AnonymousParameters([String]), Dyn), 'Function of incorrect type in file stats.py')('Input values not paired in linregress.  Aborting.')
    n = len(retic_cast(x, List(Float), Dyn, 'Argument of incorrect type in file stats.py'))
    x = retic_cast(list(retic_cast(map, Dyn, Function(AnonymousParameters([Function(DynParameters, Float), List(Float)]), Dyn), 'Function of incorrect type in file stats.py')(float, x)), List(Dyn), List(Float), 'Assignee of incorrect type in file stats.py (line 948)')
    y = retic_cast(list(retic_cast(map, Dyn, Function(AnonymousParameters([Function(DynParameters, Float), List(Float)]), Dyn), 'Function of incorrect type in file stats.py')(float, y)), List(Dyn), List(Float), 'Assignee of incorrect type in file stats.py (line 949)')
    xmean = mean(x)
    ymean = mean(y)
    r_num = float(retic_cast(((n * summult(x, y)) - (sum(x) * sum(y))), Float, Dyn, 'Argument of incorrect type in file stats.py'))
    r_den = sqrt((((n * ss(x)) - square_of_sums(x)) * ((n * ss(y)) - square_of_sums(y))))
    r = (r_num / r_den)
    z = (0.5 * log((((1.0 + r) + TINY) / ((1.0 - r) + TINY))))
    df = (n - 2)
    t = (r * sqrt((df / (((1.0 - r) + TINY) * ((1.0 + r) + TINY)))))
    prob = betai((0.5 * df), 0.5, (df / (df + (t * t))))
    slope = (r_num / float(retic_cast(((n * ss(x)) - square_of_sums(x)), Float, Dyn, 'Argument of incorrect type in file stats.py')))
    intercept = (ymean - (slope * xmean))
    sterrest = (sqrt((1 - (r * r))) * samplestdev(y))
    return (slope, intercept, r, prob, sterrest)

def ttest_1samp(a, popmean, printit=retic_cast(0, Int, Dyn, 'Default argument of incorrect type'), name=retic_cast('Sample', String, Dyn, 'Default argument of incorrect type'), writemode=retic_cast('a', String, Dyn, 'Default argument of incorrect type')) ->(float, float):
    x = mean(retic_cast(a, Dyn, List(Float), 'Argument of incorrect type in file stats.py'))
    v = var(retic_cast(a, Dyn, List(Float), 'Argument of incorrect type in file stats.py'))
    n = len(a)
    df = (n - 1)
    svar = (((n - 1) * v) / float(retic_cast(df, Int, Dyn, 'Argument of incorrect type in file stats.py')))
    t = ((x - popmean) / sqrt((svar * (1.0 / n))))
    prob = betai((0.5 * df), 0.5, retic_cast((float(retic_cast(df, Int, Dyn, 'Argument of incorrect type in file stats.py')) / (df + (t * t))), Dyn, Float, 'Argument of incorrect type in file stats.py'))
    if (printit != 0):
        statname = 'Single-sample T-test.'
        outputpairedstats(printit, retic_cast(writemode, Dyn, String, 'Argument of incorrect type in file stats.py'), retic_cast('Population', String, Dyn, 'Argument of incorrect type in file stats.py'), retic_cast('--', String, Dyn, 'Argument of incorrect type in file stats.py'), popmean, retic_cast(0, Int, Dyn, 'Argument of incorrect type in file stats.py'), retic_cast(0, Int, Dyn, 'Argument of incorrect type in file stats.py'), retic_cast(0, Int, Dyn, 'Argument of incorrect type in file stats.py'), name, retic_cast(n, Int, Dyn, 'Argument of incorrect type in file stats.py'), retic_cast(x, Float, Dyn, 'Argument of incorrect type in file stats.py'), retic_cast(v, Float, Dyn, 'Argument of incorrect type in file stats.py'), retic_cast(min, Dyn, Function(AnonymousParameters([Dyn]), Dyn), 'Function of incorrect type in file stats.py')(a), retic_cast(max, Dyn, Function(AnonymousParameters([Dyn]), Dyn), 'Function of incorrect type in file stats.py')(a), statname, t, retic_cast(prob, Float, Dyn, 'Argument of incorrect type in file stats.py'))
    return retic_cast((t, prob), Tuple(Dyn, Float), Tuple(Float, Float), 'Return value of incorrect type')

def ttest_ind(a, b, printit=retic_cast(0, Int, Dyn, 'Default argument of incorrect type'), name1=retic_cast('Samp1', String, Dyn, 'Default argument of incorrect type'), name2=retic_cast('Samp2', String, Dyn, 'Default argument of incorrect type'), writemode=retic_cast('a', String, Dyn, 'Default argument of incorrect type')) ->(float, float):
    x1 = mean(retic_cast(a, Dyn, List(Float), 'Argument of incorrect type in file stats.py'))
    x2 = mean(retic_cast(b, Dyn, List(Float), 'Argument of incorrect type in file stats.py'))
    v1 = (stdev(retic_cast(a, Dyn, List(Float), 'Argument of incorrect type in file stats.py')) ** 2)
    v2 = (stdev(retic_cast(b, Dyn, List(Float), 'Argument of incorrect type in file stats.py')) ** 2)
    n1 = len(a)
    n2 = len(b)
    df = ((n1 + n2) - 2)
    svar = ((((n1 - 1) * v1) + ((n2 - 1) * v2)) / float(retic_cast(df, Int, Dyn, 'Argument of incorrect type in file stats.py')))
    t = ((x1 - x2) / sqrt((svar * ((1.0 / n1) + (1.0 / n2)))))
    prob = betai((0.5 * df), 0.5, (df / (df + (t * t))))
    if (printit != 0):
        statname = 'Independent samples T-test.'
        outputpairedstats(printit, retic_cast(writemode, Dyn, String, 'Argument of incorrect type in file stats.py'), name1, retic_cast(n1, Int, Dyn, 'Argument of incorrect type in file stats.py'), retic_cast(x1, Float, Dyn, 'Argument of incorrect type in file stats.py'), retic_cast(v1, Float, Dyn, 'Argument of incorrect type in file stats.py'), retic_cast(min, Dyn, Function(AnonymousParameters([Dyn]), Dyn), 'Function of incorrect type in file stats.py')(a), retic_cast(max, Dyn, Function(AnonymousParameters([Dyn]), Dyn), 'Function of incorrect type in file stats.py')(a), name2, retic_cast(n2, Int, Dyn, 'Argument of incorrect type in file stats.py'), retic_cast(x2, Float, Dyn, 'Argument of incorrect type in file stats.py'), retic_cast(v2, Float, Dyn, 'Argument of incorrect type in file stats.py'), retic_cast(min, Dyn, Function(AnonymousParameters([Dyn]), Dyn), 'Function of incorrect type in file stats.py')(b), retic_cast(max, Dyn, Function(AnonymousParameters([Dyn]), Dyn), 'Function of incorrect type in file stats.py')(b), statname, retic_cast(t, Float, Dyn, 'Argument of incorrect type in file stats.py'), retic_cast(prob, Float, Dyn, 'Argument of incorrect type in file stats.py'))
    return (t, prob)

def ttest_rel(a, b, printit=retic_cast(0, Int, Dyn, 'Default argument of incorrect type'), name1=retic_cast('Sample1', String, Dyn, 'Default argument of incorrect type'), name2=retic_cast('Sample2', String, Dyn, 'Default argument of incorrect type'), writemode=retic_cast('a', String, Dyn, 'Default argument of incorrect type')) ->(float, float):
    if (len(a) != len(b)):
        raise retic_cast(ValueError, Dyn, Function(AnonymousParameters([String]), Dyn), 'Function of incorrect type in file stats.py')('Unequal length lists in ttest_rel.')
    x1 = mean(retic_cast(a, Dyn, List(Float), 'Argument of incorrect type in file stats.py'))
    x2 = mean(retic_cast(b, Dyn, List(Float), 'Argument of incorrect type in file stats.py'))
    v1 = var(retic_cast(a, Dyn, List(Float), 'Argument of incorrect type in file stats.py'))
    v2 = var(retic_cast(b, Dyn, List(Float), 'Argument of incorrect type in file stats.py'))
    n = len(a)
    cov = retic_cast(0, Int, Dyn, 'Assignee of incorrect type in file stats.py (line 1045)')
    for i in range(retic_cast(len(a), Int, Dyn, 'Argument of incorrect type in file stats.py')):
        cov = (cov + ((a[i] - x1) * (b[i] - x2)))
    df = (n - 1)
    cov = (cov / float(retic_cast(df, Int, Dyn, 'Argument of incorrect type in file stats.py')))
    sd = sqrt(retic_cast((((v1 + v2) - (2.0 * cov)) / float(retic_cast(n, Int, Dyn, 'Argument of incorrect type in file stats.py'))), Dyn, Float, 'Argument of incorrect type in file stats.py'))
    t = ((x1 - x2) / sd)
    prob = betai((0.5 * df), 0.5, (df / (df + (t * t))))
    if (printit != 0):
        statname = 'Related samples T-test.'
        outputpairedstats(printit, retic_cast(writemode, Dyn, String, 'Argument of incorrect type in file stats.py'), name1, retic_cast(n, Int, Dyn, 'Argument of incorrect type in file stats.py'), retic_cast(x1, Float, Dyn, 'Argument of incorrect type in file stats.py'), retic_cast(v1, Float, Dyn, 'Argument of incorrect type in file stats.py'), retic_cast(min, Dyn, Function(AnonymousParameters([Dyn]), Dyn), 'Function of incorrect type in file stats.py')(a), retic_cast(max, Dyn, Function(AnonymousParameters([Dyn]), Dyn), 'Function of incorrect type in file stats.py')(a), name2, retic_cast(n, Int, Dyn, 'Argument of incorrect type in file stats.py'), retic_cast(x2, Float, Dyn, 'Argument of incorrect type in file stats.py'), retic_cast(v2, Float, Dyn, 'Argument of incorrect type in file stats.py'), retic_cast(min, Dyn, Function(AnonymousParameters([Dyn]), Dyn), 'Function of incorrect type in file stats.py')(b), retic_cast(max, Dyn, Function(AnonymousParameters([Dyn]), Dyn), 'Function of incorrect type in file stats.py')(b), statname, retic_cast(t, Float, Dyn, 'Argument of incorrect type in file stats.py'), retic_cast(prob, Float, Dyn, 'Argument of incorrect type in file stats.py'))
    return (t, prob)

def chisquare(f_obs, f_exp=None) ->(float, float):
    k = len(f_obs)
    if (f_exp == None):
        f_exp = retic_cast(([(sum(retic_cast(f_obs, Dyn, List(Float), 'Argument of incorrect type in file stats.py')) / float(retic_cast(k, Int, Dyn, 'Argument of incorrect type in file stats.py')))] * len(f_obs)), List(Float), Dyn, 'Assignee of incorrect type in file stats.py (line 1074)')
    chisq = retic_cast(0, Int, Dyn, 'Assignee of incorrect type in file stats.py (line 1075)')
    for i in range(retic_cast(len(f_obs), Int, Dyn, 'Argument of incorrect type in file stats.py')):
        chisq = (chisq + (((f_obs[i] - f_exp[i]) ** 2) / float(f_exp[i])))
    return retic_cast((chisq, chisqprob(retic_cast(chisq, Dyn, Float, 'Argument of incorrect type in file stats.py'), (k - 1))), Tuple(Dyn, Float), Tuple(Float, Float), 'Return value of incorrect type')

def ks_2samp(data1: List(float), data2: List(float)) ->(float, float):
    j1 = 0
    j2 = 0
    fn1 = 0.0
    fn2 = 0.0
    n1 = len(retic_cast(data1, List(Float), Dyn, 'Argument of incorrect type in file stats.py'))
    n2 = len(retic_cast(data2, List(Float), Dyn, 'Argument of incorrect type in file stats.py'))
    en1 = n1
    en2 = n2
    d = 0.0
    retic_cast(data1.sort, Dyn, Function(AnonymousParameters([]), Dyn), 'Function of incorrect type in file stats.py')()
    retic_cast(data2.sort, Dyn, Function(AnonymousParameters([]), Dyn), 'Function of incorrect type in file stats.py')()
    while ((j1 < n1) and (j2 < n2)):
        d1 = data1[j1]
        d2 = data2[j2]
        if (d1 <= d2):
            fn1 = (j1 / float(retic_cast(en1, Int, Dyn, 'Argument of incorrect type in file stats.py')))
            j1 = (j1 + 1)
        if (d2 <= d1):
            fn2 = (j2 / float(retic_cast(en2, Int, Dyn, 'Argument of incorrect type in file stats.py')))
            j2 = (j2 + 1)
        dt = (fn2 - fn1)
        if (fabs(dt) > fabs(d)):
            d = dt
    try:
        en = sqrt(((en1 * en2) / float(retic_cast((en1 + en2), Int, Dyn, 'Argument of incorrect type in file stats.py'))))
        prob = ksprob((((en + 0.12) + (0.11 / en)) * abs(d)))
    except:
        prob = 1.0
    return (d, prob)

def mannwhitneyu(x: List(float), y: List(float)) ->(float, float):
    n1 = len(retic_cast(x, List(Float), Dyn, 'Argument of incorrect type in file stats.py'))
    n2 = len(retic_cast(y, List(Float), Dyn, 'Argument of incorrect type in file stats.py'))
    ranked = rankdata((x + y))
    rankx = ranked[0:n1]
    ranky = ranked[n1:]
    u1 = (((n1 * n2) + ((n1 * (n1 + 1)) / 2.0)) - sum(rankx))
    u2 = ((n1 * n2) - u1)
    bigu = retic_cast(max, Dyn, Function(AnonymousParameters([Float, Float]), Dyn), 'Function of incorrect type in file stats.py')(u1, u2)
    smallu = retic_cast(min, Dyn, Function(AnonymousParameters([Float, Float]), Dyn), 'Function of incorrect type in file stats.py')(u1, u2)
    proportion = (bigu / float(retic_cast((n1 * n2), Int, Dyn, 'Argument of incorrect type in file stats.py')))
    T = sqrt(tiecorrect(retic_cast(ranked, List(Float), List(Dyn), 'Argument of incorrect type in file stats.py')))
    if (T == 0):
        raise retic_cast(ValueError, Dyn, Function(AnonymousParameters([String]), Dyn), 'Function of incorrect type in file stats.py')('All numbers are identical in lmannwhitneyu')
    sd = sqrt(((((T * n1) * n2) * ((n1 + n2) + 1)) / 12.0))
    z = abs(retic_cast(((bigu - ((n1 * n2) / 2.0)) / sd), Dyn, Float, 'Argument of incorrect type in file stats.py'))
    return retic_cast((smallu, (1.0 - zprob(z))), Tuple(Dyn, Float), Tuple(Float, Float), 'Return value of incorrect type')

def tiecorrect(rankvals: List(Dyn)) ->float:
    (sorted, posn) = retic_cast(shellsort(retic_cast(rankvals, List(Dyn), List(Float), 'Argument of incorrect type in file stats.py')), Tuple(List(Float), List(Int)), Dyn, 'Assignee of incorrect type in file stats.py (line 1159)')
    n = len(retic_cast(sorted, List(Float), Dyn, 'Argument of incorrect type in file stats.py'))
    T = 0.0
    i = 0
    while (i < (n - 1)):
        if (sorted[i] == sorted[(i + 1)]):
            nties = 1
            while ((i < (n - 1)) and (sorted[i] == sorted[(i + 1)])):
                nties = (nties + 1)
                i = (i + 1)
            T = ((T + (nties ** 3)) - nties)
        i = (i + 1)
    T = (T / float(retic_cast(((n ** 3) - n), Int, Dyn, 'Argument of incorrect type in file stats.py')))
    return (1.0 - T)

def ranksums(x: List(float), y: List(float)) ->(float, float):
    n1 = len(retic_cast(x, List(Float), Dyn, 'Argument of incorrect type in file stats.py'))
    n2 = len(retic_cast(y, List(Float), Dyn, 'Argument of incorrect type in file stats.py'))
    alldata = (x + y)
    ranked = rankdata(alldata)
    x = ranked[:n1]
    y = ranked[n1:]
    s = sum(x)
    expected = ((n1 * ((n1 + n2) + 1)) / 2.0)
    z = ((s - expected) / sqrt((((n1 * n2) * ((n1 + n2) + 1)) / 12.0)))
    prob = (2 * (1.0 - zprob(abs(z))))
    return (z, prob)

def wilcoxont(x: List(float), y: List(float)) ->(float, float):
    if (len(retic_cast(x, List(Float), Dyn, 'Argument of incorrect type in file stats.py')) != len(retic_cast(y, List(Float), Dyn, 'Argument of incorrect type in file stats.py'))):
        raise retic_cast(ValueError, Dyn, Function(AnonymousParameters([String]), Dyn), 'Function of incorrect type in file stats.py')('Unequal N in wilcoxont.  Aborting.')
    d = []
    for i in range(retic_cast(len(retic_cast(x, List(Float), Dyn, 'Argument of incorrect type in file stats.py')), Int, Dyn, 'Argument of incorrect type in file stats.py')):
        diff = (x[i] - y[i])
        if (diff != 0):
            d.append(retic_cast(diff, Float, Dyn, 'Argument of incorrect type in file stats.py'))
    count = len(retic_cast(d, List(Dyn), Dyn, 'Argument of incorrect type in file stats.py'))
    absd = list(retic_cast(map, Dyn, Function(AnonymousParameters([Function(NamedParameters([('x', Float)]), Float), List(Dyn)]), Dyn), 'Function of incorrect type in file stats.py')(abs, d))
    absranked = rankdata(retic_cast(absd, List(Dyn), List(Float), 'Argument of incorrect type in file stats.py'))
    r_plus = 0.0
    r_minus = 0.0
    for i in range(retic_cast(len(retic_cast(absd, List(Dyn), Dyn, 'Argument of incorrect type in file stats.py')), Int, Dyn, 'Argument of incorrect type in file stats.py')):
        if (d[i] < 0):
            r_minus = (r_minus + absranked[i])
        else:
            r_plus = (r_plus + absranked[i])
    wt = retic_cast(min, Dyn, Function(AnonymousParameters([Float, Float]), Dyn), 'Function of incorrect type in file stats.py')(r_plus, r_minus)
    mn = ((count * (count + 1)) * 0.25)
    se = sqrt((((count * (count + 1)) * ((2.0 * count) + 1.0)) / 24.0))
    z = (fabs(retic_cast((wt - mn), Dyn, Float, 'Argument of incorrect type in file stats.py')) / se)
    prob = (2 * (1.0 - zprob(abs(z))))
    return retic_cast((wt, prob), Tuple(Dyn, Float), Tuple(Float, Float), 'Return value of incorrect type')

def kruskalwallish(*args) ->(float, float):
    args = retic_cast(list(args), List(Dyn), Dyn, 'Assignee of incorrect type in file stats.py (line 1240)')
    n = retic_cast(([0] * len(args)), List(Int), List(Dyn), 'Assignee of incorrect type in file stats.py (line 1241)')
    all = retic_cast([], List(Dyn), Dyn, 'Assignee of incorrect type in file stats.py (line 1242)')
    n = list(retic_cast(map, Dyn, Function(AnonymousParameters([Function(DynParameters, Int), Dyn]), Dyn), 'Function of incorrect type in file stats.py')(len, args))
    for i in range(retic_cast(len(args), Int, Dyn, 'Argument of incorrect type in file stats.py')):
        all = (all + args[i])
    ranked = rankdata(retic_cast(all, Dyn, List(Float), 'Argument of incorrect type in file stats.py'))
    T = tiecorrect(retic_cast(ranked, List(Float), List(Dyn), 'Argument of incorrect type in file stats.py'))
    for i in range(retic_cast(len(args), Int, Dyn, 'Argument of incorrect type in file stats.py')):
        args[i] = retic_cast(ranked[0:retic_cast(n[i], Dyn, Int, 'Indexing with non-integer type')], List(Float), Dyn, 'Assignee of incorrect type in file stats.py (line 1249)')
        ranked[0:retic_cast(n[i], Dyn, Int, 'Indexing with non-integer type')]
        del ranked[0:n[i]]
    rsums = []
    for i in range(retic_cast(len(args), Int, Dyn, 'Argument of incorrect type in file stats.py')):
        rsums.append(retic_cast((sum(retic_cast(args[i], Dyn, List(Float), 'Argument of incorrect type in file stats.py')) ** 2), Float, Dyn, 'Argument of incorrect type in file stats.py'))
        rsums[i] = (rsums[i] / float(n[i]))
    ssbn = sum(retic_cast(rsums, List(Dyn), List(Float), 'Argument of incorrect type in file stats.py'))
    totaln = sum(retic_cast(n, List(Dyn), List(Float), 'Argument of incorrect type in file stats.py'))
    h = (((12.0 / (totaln * (totaln + 1))) * ssbn) - (3 * (totaln + 1)))
    df = (len(args) - 1)
    if (T == 0):
        raise retic_cast(ValueError, Dyn, Function(AnonymousParameters([String]), Dyn), 'Function of incorrect type in file stats.py')('All numbers are identical in lkruskalwallish')
    h = (h / float(retic_cast(T, Float, Dyn, 'Argument of incorrect type in file stats.py')))
    return (h, chisqprob(h, df))

def friedmanchisquare(*args) ->(float, float):
    k = len(args)
    if (k < 3):
        raise retic_cast(ValueError, Dyn, Function(AnonymousParameters([String]), Dyn), 'Function of incorrect type in file stats.py')('Less than 3 levels.  Friedman test not appropriate.')
    n = len(args[0])
    data = pstat.abut(*tuple(args))
    for i in range(retic_cast(len(retic_cast(data, List(Dyn), Dyn, 'Argument of incorrect type in file stats.py')), Int, Dyn, 'Argument of incorrect type in file stats.py')):
        data[i] = retic_cast(rankdata(retic_cast(data[i], Dyn, List(Float), 'Argument of incorrect type in file stats.py')), List(Float), Dyn, 'Assignee of incorrect type in file stats.py (line 1283)')
    ssbn = 0
    for i in range(retic_cast(k, Int, Dyn, 'Argument of incorrect type in file stats.py')):
        ssbn = (ssbn + (sum(retic_cast(args[i], Dyn, List(Float), 'Argument of incorrect type in file stats.py')) ** 2))
    chisq = (((12.0 / ((k * n) * (k + 1))) * ssbn) - ((3 * n) * (k + 1)))
    return (chisq, chisqprob(chisq, (k - 1)))

def chisqprob(chisq: float, df: int) ->float:
    BIG = 20.0

    def ex(x: float) ->float:
        BIG = 20.0
        if (x < (- BIG)):
            return 0.0
        else:
            return exp(x)
    if ((chisq <= 0) or (df < 1)):
        return 1.0
    a = (0.5 * chisq)
    if ((df % 2) == 0):
        even = 1
    else:
        even = 0
    if (df > 1):
        y = ex((- a))
    if even:
        s = y
    else:
        s = (2.0 * zprob((- sqrt(chisq))))
    if (df > 2):
        chisq = (0.5 * (df - 1.0))
        if even:
            z = 1.0
        else:
            z = 0.5
        if (a > BIG):
            if even:
                e = 0.0
            else:
                e = log(sqrt(pi))
            c = log(a)
            while (z <= chisq):
                e = (log(z) + e)
                s = (s + ex((((c * z) - a) - e)))
                z = (z + 1.0)
            return s
        else:
            if even:
                e = 1.0
            else:
                e = ((1.0 / sqrt(pi)) / sqrt(a))
            c = 0.0
            while (z <= chisq):
                e = (e * (a / float(retic_cast(z, Float, Dyn, 'Argument of incorrect type in file stats.py'))))
                c = (c + e)
                z = (z + 1.0)
            return ((c * y) + s)
    else:
        return s

def erfcc(x: float) ->float:
    z = abs(x)
    t = (1.0 / (1.0 + (0.5 * z)))
    ans = (t * exp(((((- z) * z) - 1.26551223) + (t * (1.00002368 + (t * (0.37409196 + (t * (0.09678418 + (t * ((- 0.18628806) + (t * (0.27886807 + (t * ((- 1.13520398) + (t * (1.48851587 + (t * ((- 0.82215223) + (t * 0.17087277))))))))))))))))))))
    if (x >= 0):
        return ans
    else:
        return (2.0 - ans)

def zprob(z: float) ->float:
    Z_MAX = 6.0
    if (z == 0.0):
        x = 0.0
    else:
        y = (0.5 * fabs(z))
        if (y >= (Z_MAX * 0.5)):
            x = 1.0
        elif (y < 1.0):
            w = (y * y)
            x = ((((((((((((((((((0.000124818987 * w) - 0.001075204047) * w) + 0.005198775019) * w) - 0.019198292004) * w) + 0.059054035642) * w) - 0.151968751364) * w) + 0.319152932694) * w) - 0.5319230073) * w) + 0.797884560593) * y) * 2.0)
        else:
            y = (y - 2.0)
            x = (((((((((((((((((((((((((((((- 4.5255659e-05) * y) + 0.00015252929) * y) - 1.9538132e-05) * y) - 0.000676904986) * y) + 0.001390604284) * y) - 0.00079462082) * y) - 0.002034254874) * y) + 0.006549791214) * y) - 0.010557625006) * y) + 0.011630447319) * y) - 0.009279453341) * y) + 0.005353579108) * y) - 0.002141268741) * y) + 0.000535310849) * y) + 0.999936657524)
    if (z > 0.0):
        prob = ((x + 1.0) * 0.5)
    else:
        prob = ((1.0 - x) * 0.5)
    return prob

def ksprob(alam: float) ->float:
    fac = retic_cast(2.0, Float, Dyn, 'Assignee of incorrect type in file stats.py (line 1420)')
    sum = retic_cast(0.0, Float, Dyn, 'Assignee of incorrect type in file stats.py (line 1421)')
    termbf = 0.0
    a2 = (((- 2.0) * alam) * alam)
    for j in range(retic_cast(1, Int, Dyn, 'Argument of incorrect type in file stats.py'), retic_cast(201, Int, Dyn, 'Argument of incorrect type in file stats.py')):
        term = (fac * exp(((a2 * j) * j)))
        sum = (sum + term)
        if ((fabs(retic_cast(term, Dyn, Float, 'Argument of incorrect type in file stats.py')) <= (0.001 * termbf)) or (fabs(retic_cast(term, Dyn, Float, 'Argument of incorrect type in file stats.py')) < (1e-08 * sum))):
            return retic_cast(sum, Dyn, Float, 'Return value of incorrect type')
        fac = (- fac)
        termbf = fabs(retic_cast(term, Dyn, Float, 'Argument of incorrect type in file stats.py'))
    return 1.0

def fprob(dfnum: float, dfden: float, F: float) ->float:
    p = betai((0.5 * dfden), (0.5 * dfnum), (dfden / float(retic_cast((dfden + (dfnum * F)), Float, Dyn, 'Argument of incorrect type in file stats.py'))))
    return p

def betacf(a: float, b: float, x: float) ->float:
    ITMAX = 200
    EPS = 3e-07
    bm = az = am = 1.0
    qab = (a + b)
    qap = (a + 1.0)
    qam = (a - 1.0)
    bz = (1.0 - ((qab * x) / qap))
    for i in range(retic_cast((ITMAX + 1), Int, Dyn, 'Argument of incorrect type in file stats.py')):
        em = float(retic_cast((i + 1), Int, Dyn, 'Argument of incorrect type in file stats.py'))
        tem = (em + em)
        d = (((em * (b - em)) * x) / ((qam + tem) * (a + tem)))
        ap = (az + (d * am))
        bp = (bz + (d * bm))
        d = ((((- (a + em)) * (qab + em)) * x) / ((qap + tem) * (a + tem)))
        app = (ap + (d * az))
        bpp = (bp + (d * bz))
        aold = az
        am = (ap / bpp)
        bm = (bp / bpp)
        az = (app / bpp)
        bz = 1.0
        if (abs((az - aold)) < (EPS * abs(az))):
            return az
    retic_cast(print, Dyn, Function(AnonymousParameters([String]), Dyn), 'Function of incorrect type in file stats.py')('a or b too big, or ITMAX too small in Betacf.')
    raise Exception

def gammln(xx: float) ->float:
    coeff = [76.18009173, (- 86.50532033), 24.01409822, (- 1.231739516), 0.00120858003, (- 5.36382e-06)]
    x = (xx - 1.0)
    tmp = (x + 5.5)
    tmp = (tmp - ((x + 0.5) * log(tmp)))
    ser = 1.0
    for j in range(retic_cast(len(retic_cast(coeff, List(Float), Dyn, 'Argument of incorrect type in file stats.py')), Int, Dyn, 'Argument of incorrect type in file stats.py')):
        x = (x + 1)
        ser = (ser + (coeff[j] / x))
    return ((- tmp) + log((2.50662827465 * ser)))

def betai(a: float, b: float, x: float) ->float:
    if ((x < 0.0) or (x > 1.0)):
        raise retic_cast(ValueError, Dyn, Function(AnonymousParameters([String]), Dyn), 'Function of incorrect type in file stats.py')('Bad x in lbetai')
    if ((x == 0.0) or (x == 1.0)):
        bt = 0.0
    else:
        bt = exp(((((gammln((a + b)) - gammln(a)) - gammln(b)) + (a * log(x))) + (b * log((1.0 - x)))))
    if (x < ((a + 1.0) / ((a + b) + 2.0))):
        return ((bt * betacf(a, b, x)) / float(retic_cast(a, Float, Dyn, 'Argument of incorrect type in file stats.py')))
    else:
        return (1.0 - ((bt * betacf(b, a, (1.0 - x))) / float(retic_cast(b, Float, Dyn, 'Argument of incorrect type in file stats.py'))))

def F_oneway(*lists) ->(float, float):
    a = len(lists)
    means = retic_cast(([0] * a), List(Int), Dyn, 'Assignee of incorrect type in file stats.py (line 1541)')
    vars = retic_cast(([0] * a), List(Int), Dyn, 'Assignee of incorrect type in file stats.py (line 1542)')
    ns = retic_cast(([0] * a), List(Int), Dyn, 'Assignee of incorrect type in file stats.py (line 1543)')
    alldata = retic_cast([], List(Dyn), Dyn, 'Assignee of incorrect type in file stats.py (line 1544)')
    tmp = retic_cast(list, Dyn, Function(AnonymousParameters([Dyn]), Dyn), 'Function of incorrect type in file stats.py')(retic_cast(map, Dyn, Function(AnonymousParameters([Dyn, Dyn]), Dyn), 'Function of incorrect type in file stats.py')(retic_cast(N, Dyn, Object('', {'array': Dyn, }), 'Attempting to access nonexistant attribute in file stats.py').array, lists))
    means = retic_cast(list, Dyn, Function(AnonymousParameters([Dyn]), Dyn), 'Function of incorrect type in file stats.py')(retic_cast(map, Dyn, Function(AnonymousParameters([Dyn, Dyn]), Dyn), 'Function of incorrect type in file stats.py')(amean, tmp))
    vars = retic_cast(list, Dyn, Function(AnonymousParameters([Dyn]), Dyn), 'Function of incorrect type in file stats.py')(retic_cast(map, Dyn, Function(AnonymousParameters([Dyn, Dyn]), Dyn), 'Function of incorrect type in file stats.py')(avar, tmp))
    ns = retic_cast(list, Dyn, Function(AnonymousParameters([Dyn]), Dyn), 'Function of incorrect type in file stats.py')(retic_cast(map, Dyn, Function(AnonymousParameters([Function(DynParameters, Int), Dyn]), Dyn), 'Function of incorrect type in file stats.py')(len, lists))
    for i in range(retic_cast(len(lists), Int, Dyn, 'Argument of incorrect type in file stats.py')):
        alldata = (alldata + lists[i])
    alldata = retic_cast(retic_cast(N, Dyn, Object('', {'array': Dyn, }), 'Attempting to access nonexistant attribute in file stats.py').array, Dyn, Function(AnonymousParameters([Dyn]), Dyn), 'Function of incorrect type in file stats.py')(alldata)
    bign = len(alldata)
    sstot = (retic_cast(ass, Dyn, Function(AnonymousParameters([Dyn]), Dyn), 'Function of incorrect type in file stats.py')(alldata) - (retic_cast(asquare_of_sums, Dyn, Function(AnonymousParameters([Dyn]), Dyn), 'Function of incorrect type in file stats.py')(alldata) / float(retic_cast(bign, Int, Dyn, 'Argument of incorrect type in file stats.py'))))
    ssbn = retic_cast(0, Int, Dyn, 'Assignee of incorrect type in file stats.py (line 1554)')
    for list in lists:
        ssbn = (ssbn + (retic_cast(asquare_of_sums, Dyn, Function(AnonymousParameters([Dyn]), Dyn), 'Function of incorrect type in file stats.py')(retic_cast(retic_cast(N, Dyn, Object('', {'array': Dyn, }), 'Attempting to access nonexistant attribute in file stats.py').array, Dyn, Function(AnonymousParameters([Dyn]), Dyn), 'Function of incorrect type in file stats.py')(list)) / float(retic_cast(len(list), Int, Dyn, 'Argument of incorrect type in file stats.py'))))
    ssbn = (ssbn - (retic_cast(asquare_of_sums, Dyn, Function(AnonymousParameters([Dyn]), Dyn), 'Function of incorrect type in file stats.py')(alldata) / float(retic_cast(bign, Int, Dyn, 'Argument of incorrect type in file stats.py'))))
    sswn = (sstot - ssbn)
    dfbn = (a - 1)
    dfwn = (bign - a)
    msb = (ssbn / float(retic_cast(dfbn, Int, Dyn, 'Argument of incorrect type in file stats.py')))
    msw = (sswn / float(retic_cast(dfwn, Int, Dyn, 'Argument of incorrect type in file stats.py')))
    f = (msb / msw)
    prob = fprob(dfbn, dfwn, retic_cast(f, Dyn, Float, 'Argument of incorrect type in file stats.py'))
    return retic_cast((f, prob), Tuple(Dyn, Float), Tuple(Float, Float), 'Return value of incorrect type')

def F_value(ER: float, EF: float, dfnum: float, dfden: float) ->float:
    return (((ER - EF) / float(retic_cast(dfnum, Float, Dyn, 'Argument of incorrect type in file stats.py'))) / (EF / float(retic_cast(dfden, Float, Dyn, 'Argument of incorrect type in file stats.py'))))

def writecc(listoflists, file, writetype=retic_cast('w', String, Dyn, 'Default argument of incorrect type'), extra=retic_cast(2, Int, Dyn, 'Default argument of incorrect type')):
    if (retic_cast(type, Dyn, Function(AnonymousParameters([Dyn]), Dyn), 'Function of incorrect type in file stats.py')(listoflists[0]) not in [list, tuple]):
        listoflists = retic_cast([listoflists], List(Dyn), Dyn, 'Assignee of incorrect type in file stats.py (line 1595)')
    outfile = retic_cast(open, Dyn, Function(AnonymousParameters([Dyn, Dyn]), Dyn), 'Function of incorrect type in file stats.py')(file, writetype)
    rowstokill = []
    list2print = retic_cast(retic_cast(copy, Dyn, Object('', {'deepcopy': Dyn, }), 'Attempting to access nonexistant attribute in file stats.py').deepcopy, Dyn, Function(AnonymousParameters([Dyn]), Dyn), 'Function of incorrect type in file stats.py')(listoflists)
    for i in range(retic_cast(len(listoflists), Int, Dyn, 'Argument of incorrect type in file stats.py')):
        if ((listoflists[i] == ['\n']) or (listoflists[i] == '\n') or (listoflists[i] == 'dashes')):
            rowstokill = (rowstokill + [i])
    retic_cast(rowstokill.reverse, Dyn, Function(AnonymousParameters([]), Dyn), 'Function of incorrect type in file stats.py')()
    for row in rowstokill:
        list2print[row]
        del list2print[row]
    maxsize = ([0] * len(list2print[0]))
    for col in range(retic_cast(len(list2print[0]), Int, Dyn, 'Argument of incorrect type in file stats.py')):
        items = pstat.colex(retic_cast(list2print, Dyn, List(List(Dyn)), 'Argument of incorrect type in file stats.py'), retic_cast(col, Int, Dyn, 'Argument of incorrect type in file stats.py'))
        items = retic_cast(list(retic_cast(map, Dyn, Function(AnonymousParameters([Function(NamedParameters([('x', Dyn)]), String), Dyn]), Dyn), 'Function of incorrect type in file stats.py')(pstat.makestr, items)), List(Dyn), Dyn, 'Assignee of incorrect type in file stats.py (line 1608)')
        maxsize[col] = retic_cast((retic_cast(max, Dyn, Function(AnonymousParameters([List(Dyn)]), Dyn), 'Function of incorrect type in file stats.py')(list(retic_cast(map, Dyn, Function(AnonymousParameters([Function(DynParameters, Int), Dyn]), Dyn), 'Function of incorrect type in file stats.py')(len, items))) + extra), Dyn, Int, 'Assignee of incorrect type in file stats.py (line 1609)')
    for row in listoflists:
        if ((row == ['\n']) or (row == '\n')):
            retic_cast(retic_cast(outfile, Dyn, Object('', {'write': Dyn, }), 'Attempting to access nonexistant attribute in file stats.py').write, Dyn, Function(AnonymousParameters([String]), Dyn), 'Function of incorrect type in file stats.py')('\n')
        elif ((row == ['dashes']) or (row == 'dashes')):
            dashes = dyn(retic_cast(([0] * len(retic_cast(maxsize, List(Int), Dyn, 'Argument of incorrect type in file stats.py'))), List(Int), Dyn, 'Argument of incorrect type in file stats.py'))
            for j in range(retic_cast(len(retic_cast(maxsize, List(Int), Dyn, 'Argument of incorrect type in file stats.py')), Int, Dyn, 'Argument of incorrect type in file stats.py')):
                dashes[j] = retic_cast(('-' * (maxsize[j] - 2)), String, Dyn, 'Assignee of incorrect type in file stats.py (line 1616)')
            retic_cast(retic_cast(outfile, Dyn, Object('', {'write': Dyn, }), 'Attempting to access nonexistant attribute in file stats.py').write, Dyn, Function(AnonymousParameters([String]), Dyn), 'Function of incorrect type in file stats.py')(pstat.lineincustcols(retic_cast(dashes, Dyn, List(Dyn), 'Argument of incorrect type in file stats.py'), maxsize))
        else:
            retic_cast(retic_cast(outfile, Dyn, Object('', {'write': Dyn, }), 'Attempting to access nonexistant attribute in file stats.py').write, Dyn, Function(AnonymousParameters([String]), Dyn), 'Function of incorrect type in file stats.py')(pstat.lineincustcols(retic_cast(row, Dyn, List(Dyn), 'Argument of incorrect type in file stats.py'), maxsize))
        retic_cast(retic_cast(outfile, Dyn, Object('', {'write': Dyn, }), 'Attempting to access nonexistant attribute in file stats.py').write, Dyn, Function(AnonymousParameters([String]), Dyn), 'Function of incorrect type in file stats.py')('\n')
    retic_cast(retic_cast(outfile, Dyn, Object('', {'close': Dyn, }), 'Attempting to access nonexistant attribute in file stats.py').close, Dyn, Function(AnonymousParameters([]), Dyn), 'Function of incorrect type in file stats.py')()
    return None

def incr(l, cap):
    l[0] = (l[0] + 1)
    for i in range(retic_cast(len(l), Int, Dyn, 'Argument of incorrect type in file stats.py')):
        if ((l[i] > cap[i]) and (i < (len(l) - 1))):
            l[i] = retic_cast(0, Int, Dyn, 'Assignee of incorrect type in file stats.py (line 1635)')
            l[(i + 1)] = (l[(i + 1)] + 1)
        elif ((l[i] > cap[i]) and (i == (len(l) - 1))):
            l = retic_cast((- 1), Int, Dyn, 'Assignee of incorrect type in file stats.py (line 1638)')
    return l

def sum(inlist: List(float)) ->float:
    s = 0
    for item in inlist:
        s = (s + item)
    return s

def cumsum(inlist: List(float)) ->List(float):
    newlist = retic_cast(retic_cast(copy, Dyn, Object('', {'deepcopy': Dyn, }), 'Attempting to access nonexistant attribute in file stats.py').deepcopy, Dyn, Function(AnonymousParameters([List(Float)]), Dyn), 'Function of incorrect type in file stats.py')(inlist)
    for i in range(retic_cast(1, Int, Dyn, 'Argument of incorrect type in file stats.py'), retic_cast(len(newlist), Int, Dyn, 'Argument of incorrect type in file stats.py')):
        newlist[i] = (newlist[i] + newlist[(i - 1)])
    return retic_cast(newlist, Dyn, List(Float), 'Return value of incorrect type')

def ss(inlist: List(float)) ->float:
    _ss = 0
    for item in inlist:
        _ss = (_ss + (item * item))
    return _ss

def summult(list1: List(float), list2: List(float)) ->float:
    if (len(retic_cast(list1, List(Float), Dyn, 'Argument of incorrect type in file stats.py')) != len(retic_cast(list2, List(Float), Dyn, 'Argument of incorrect type in file stats.py'))):
        raise retic_cast(ValueError, Dyn, Function(AnonymousParameters([String]), Dyn), 'Function of incorrect type in file stats.py')('Lists not equal length in summult.')
    s = retic_cast(0, Int, Dyn, 'Assignee of incorrect type in file stats.py (line 1690)')
    for (item1, item2) in pstat.abut(retic_cast(list1, List(Float), Dyn, 'Argument of incorrect type in file stats.py'), retic_cast(list2, List(Float), Dyn, 'Argument of incorrect type in file stats.py')):
        s = (s + (item1 * item2))
    return retic_cast(s, Dyn, Float, 'Return value of incorrect type')

def sumdiffsquared(x: List(float), y: List(float)) ->float:
    sds = 0
    for i in range(retic_cast(len(retic_cast(x, List(Float), Dyn, 'Argument of incorrect type in file stats.py')), Int, Dyn, 'Argument of incorrect type in file stats.py')):
        sds = (sds + ((x[i] - y[i]) ** 2))
    return sds

def square_of_sums(inlist: List(float)) ->float:
    s = sum(inlist)
    return (float(retic_cast(s, Float, Dyn, 'Argument of incorrect type in file stats.py')) * s)

def shellsort(inlist: List(float)) ->(List(float), List(int)):
    n = len(retic_cast(inlist, List(Float), Dyn, 'Argument of incorrect type in file stats.py'))
    svec = retic_cast(retic_cast(copy, Dyn, Object('', {'deepcopy': Dyn, }), 'Attempting to access nonexistant attribute in file stats.py').deepcopy, Dyn, Function(AnonymousParameters([List(Float)]), Dyn), 'Function of incorrect type in file stats.py')(inlist)
    ivec = list(retic_cast(range(retic_cast(n, Int, Dyn, 'Argument of incorrect type in file stats.py')), List(Int), Dyn, 'Argument of incorrect type in file stats.py'))
    gap = (n // 2)
    while (gap > 0):
        for i in range(retic_cast(gap, Int, Dyn, 'Argument of incorrect type in file stats.py'), retic_cast(n, Int, Dyn, 'Argument of incorrect type in file stats.py')):
            for j in range(retic_cast((i - gap), Int, Dyn, 'Argument of incorrect type in file stats.py'), retic_cast((- 1), Int, Dyn, 'Argument of incorrect type in file stats.py'), retic_cast((- gap), Int, Dyn, 'Argument of incorrect type in file stats.py')):
                while ((j >= 0) and (svec[j] > svec[(j + gap)])):
                    temp = svec[j]
                    svec[j] = svec[(j + gap)]
                    svec[(j + gap)] = temp
                    itemp = ivec[j]
                    ivec[j] = ivec[(j + gap)]
                    ivec[(j + gap)] = itemp
        gap = (gap // 2)
    return retic_cast((svec, ivec), Tuple(Dyn, List(Dyn)), Tuple(List(Float), List(Int)), 'Return value of incorrect type')

def rankdata(inlist: List(float)) ->List(float):
    n = len(retic_cast(inlist, List(Float), Dyn, 'Argument of incorrect type in file stats.py'))
    (svec, ivec) = retic_cast(shellsort(inlist), Tuple(List(Float), List(Int)), Dyn, 'Assignee of incorrect type in file stats.py (line 1757)')
    sumranks = 0
    dupcount = 0
    newlist = ([0.0] * n)
    for i in range(retic_cast(n, Int, Dyn, 'Argument of incorrect type in file stats.py')):
        sumranks = (sumranks + i)
        dupcount = (dupcount + 1)
        if ((i == (n - 1)) or (svec[i] != svec[(i + 1)])):
            averank = ((sumranks / float(retic_cast(dupcount, Int, Dyn, 'Argument of incorrect type in file stats.py'))) + 1)
            for j in range(retic_cast(((i - dupcount) + 1), Int, Dyn, 'Argument of incorrect type in file stats.py'), retic_cast((i + 1), Int, Dyn, 'Argument of incorrect type in file stats.py')):
                newlist[ivec[j]] = averank
            sumranks = 0
            dupcount = 0
    return newlist

def outputpairedstats(fname, writemode: str, name1, n1, m1, se1, min1, max1, name2, n2, m2, se2, min2, max2, statname: str, stat, prob):
    suffix = ''
    try:
        x = retic_cast(prob, Dyn, Object('', {'shape': Dyn, }), 'Attempting to access nonexistant attribute in file stats.py').shape
        prob = prob[0]
    except:
        pass
    if (prob < 0.001):
        suffix = '  ***'
    elif (prob < 0.01):
        suffix = '  **'
    elif (prob < 0.05):
        suffix = '  *'
    title = [['Name', 'N', 'Mean', 'SD', 'Min', 'Max']]
    lofl = (title + [[name1, n1, round(m1, retic_cast(3, Int, Dyn, 'Argument of incorrect type in file stats.py')), round(retic_cast(sqrt(retic_cast(se1, Dyn, Float, 'Argument of incorrect type in file stats.py')), Float, Dyn, 'Argument of incorrect type in file stats.py'), retic_cast(3, Int, Dyn, 'Argument of incorrect type in file stats.py')), min1, max1], [name2, n2, round(m2, retic_cast(3, Int, Dyn, 'Argument of incorrect type in file stats.py')), round(retic_cast(sqrt(retic_cast(se2, Dyn, Float, 'Argument of incorrect type in file stats.py')), Float, Dyn, 'Argument of incorrect type in file stats.py'), retic_cast(3, Int, Dyn, 'Argument of incorrect type in file stats.py')), min2, max2]])
    if ((retic_cast(type, Dyn, Function(AnonymousParameters([Dyn]), Dyn), 'Function of incorrect type in file stats.py')(fname) != str) or (len(fname) == 0)):
        retic_cast(print, Dyn, Function(AnonymousParameters([]), Dyn), 'Function of incorrect type in file stats.py')()
        retic_cast(print, Dyn, Function(AnonymousParameters([String]), Dyn), 'Function of incorrect type in file stats.py')(statname)
        retic_cast(print, Dyn, Function(AnonymousParameters([]), Dyn), 'Function of incorrect type in file stats.py')()
        pstat.printcc(retic_cast(lofl, List(List(Dyn)), Dyn, 'Argument of incorrect type in file stats.py'))
        retic_cast(print, Dyn, Function(AnonymousParameters([]), Dyn), 'Function of incorrect type in file stats.py')()
        try:
            if (retic_cast(stat, Dyn, Object('', {'shape': Dyn, }), 'Attempting to access nonexistant attribute in file stats.py').shape == ()):
                stat = stat[0]
            if (retic_cast(prob, Dyn, Object('', {'shape': Dyn, }), 'Attempting to access nonexistant attribute in file stats.py').shape == ()):
                prob = prob[0]
        except:
            pass
        retic_cast(print, Dyn, Function(AnonymousParameters([String, Float, String, Float, String]), Dyn), 'Function of incorrect type in file stats.py')('Test statistic = ', round(stat, retic_cast(3, Int, Dyn, 'Argument of incorrect type in file stats.py')), '   p = ', round(prob, retic_cast(3, Int, Dyn, 'Argument of incorrect type in file stats.py')), suffix)
        retic_cast(print, Dyn, Function(AnonymousParameters([]), Dyn), 'Function of incorrect type in file stats.py')()
    else:
        file = retic_cast(open, Dyn, Function(AnonymousParameters([Dyn, String]), Dyn), 'Function of incorrect type in file stats.py')(fname, writemode)
        retic_cast(retic_cast(file, Dyn, Object('', {'write': Dyn, }), 'Attempting to access nonexistant attribute in file stats.py').write, Dyn, Function(AnonymousParameters([String]), Dyn), 'Function of incorrect type in file stats.py')((('\n' + statname) + '\n\n'))
        retic_cast(retic_cast(file, Dyn, Object('', {'close': Dyn, }), 'Attempting to access nonexistant attribute in file stats.py').close, Dyn, Function(AnonymousParameters([]), Dyn), 'Function of incorrect type in file stats.py')()
        writecc(retic_cast(lofl, List(List(Dyn)), Dyn, 'Argument of incorrect type in file stats.py'), fname, retic_cast('a', String, Dyn, 'Argument of incorrect type in file stats.py'))
        file = retic_cast(open, Dyn, Function(AnonymousParameters([Dyn, String]), Dyn), 'Function of incorrect type in file stats.py')(fname, 'a')
        try:
            if (retic_cast(stat, Dyn, Object('', {'shape': Dyn, }), 'Attempting to access nonexistant attribute in file stats.py').shape == ()):
                stat = stat[0]
            if (retic_cast(prob, Dyn, Object('', {'shape': Dyn, }), 'Attempting to access nonexistant attribute in file stats.py').shape == ()):
                prob = prob[0]
        except:
            pass
        retic_cast(retic_cast(file, Dyn, Object('', {'write': Dyn, }), 'Attempting to access nonexistant attribute in file stats.py').write, Dyn, Function(AnonymousParameters([String]), Dyn), 'Function of incorrect type in file stats.py')(pstat.list2string(retic_cast(['\nTest statistic = ', round(stat, retic_cast(4, Int, Dyn, 'Argument of incorrect type in file stats.py')), '   p = ', round(prob, retic_cast(4, Int, Dyn, 'Argument of incorrect type in file stats.py')), suffix, '\n\n'], List(Dyn), Dyn, 'Argument of incorrect type in file stats.py')))
        retic_cast(retic_cast(file, Dyn, Object('', {'close': Dyn, }), 'Attempting to access nonexistant attribute in file stats.py').close, Dyn, Function(AnonymousParameters([]), Dyn), 'Function of incorrect type in file stats.py')()
    return None

def findwithin(data: List(List(Dyn))) ->int:
    numfact = (len(retic_cast(data[0], List(Dyn), Dyn, 'Argument of incorrect type in file stats.py')) - 1)
    withinvec = 0
    for col in range(retic_cast(1, Int, Dyn, 'Argument of incorrect type in file stats.py'), retic_cast(numfact, Int, Dyn, 'Argument of incorrect type in file stats.py')):
        examplelevel = pstat.unique(retic_cast(pstat.colex(data, retic_cast(col, Int, Dyn, 'Argument of incorrect type in file stats.py')), Dyn, List(Dyn), 'Argument of incorrect type in file stats.py'))[0]
        rows = pstat.linexand(data, retic_cast(col, Int, Dyn, 'Argument of incorrect type in file stats.py'), examplelevel)
        factsubjs = pstat.unique(retic_cast(pstat.colex(rows, retic_cast(0, Int, Dyn, 'Argument of incorrect type in file stats.py')), Dyn, List(Dyn), 'Argument of incorrect type in file stats.py'))
        allsubjs = pstat.unique(retic_cast(pstat.colex(data, retic_cast(0, Int, Dyn, 'Argument of incorrect type in file stats.py')), Dyn, List(Dyn), 'Argument of incorrect type in file stats.py'))
        if (len(retic_cast(factsubjs, List(Dyn), Dyn, 'Argument of incorrect type in file stats.py')) == len(retic_cast(allsubjs, List(Dyn), Dyn, 'Argument of incorrect type in file stats.py'))):
            withinvec = (withinvec + (1 << col))
    return withinvec
