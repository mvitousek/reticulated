from imp import reload
import stats, os, pstat
reload(stats)

l = list(map(float,range(1,21)))
lf = list(map(float,range(1,21)))
lf[2] = 3.0
ll = [l]*5

print('\nCENTRAL TENDENCY')
print('geometricmean:',stats.geometricmean(l), stats.geometricmean(lf), stats.geometricmean(l), stats.geometricmean(lf))
print('harmonicmean:',stats.harmonicmean(l), stats.harmonicmean(lf), stats.harmonicmean(l), stats.harmonicmean(lf))
print('mean:',stats.mean(l), stats.mean(lf), stats.mean(l), stats.mean(lf))
print('median:',stats.median(l),stats.median(lf),stats.median(l),stats.median(lf))
print('medianscore:',stats.medianscore(l),stats.medianscore(lf),stats.medianscore(l),stats.medianscore(lf))
print('mode:',stats.mode(l),stats.mode(l))

print('\nMOMENTS')
print('moment:',stats.moment(l),stats.moment(lf),stats.moment(l),stats.moment(lf))
print('variation:',stats.variation(l),stats.variation(l),stats.variation(lf),stats.variation(lf))
print('skew:',stats.skew(l),stats.skew(lf),stats.skew(l),stats.skew(lf))
print('kurtosis:',stats.kurtosis(l),stats.kurtosis(lf),stats.kurtosis(l),stats.kurtosis(lf))
print('describe:')
print(stats.describe(l))
print(stats.describe(lf))

print('\nFREQUENCY')
print('freqtable:')
print('itemfreq:')
print(stats.itemfreq(l))
print(stats.itemfreq(l))
print('scoreatpercentile:',stats.scoreatpercentile(l,40),stats.scoreatpercentile(lf,40),stats.scoreatpercentile(l,40),stats.scoreatpercentile(lf,40))
print('percentileofscore:',stats.percentileofscore(l,12),stats.percentileofscore(lf,12),stats.percentileofscore(l,12),stats.percentileofscore(lf,12))
print('histogram:',stats.histogram(l),stats.histogram(l))
print('cumfreq:')
print(stats.cumfreq(l))
print(stats.cumfreq(lf))
print(stats.cumfreq(l))
print(stats.cumfreq(lf))
print('relfreq:')
print(stats.relfreq(l))
print(stats.relfreq(lf))
print(stats.relfreq(l))
print(stats.relfreq(lf))

print('\nVARIATION')
print('obrientransform:')

l = [float(f) for f in list(range(1,21))]
ll = [l]*5

print(stats.obrientransform(l,l,l,l,l))

print('samplevar:',stats.samplevar(l),stats.samplevar(l))
print('samplestdev:',stats.samplestdev(l),stats.samplestdev(l))
print('var:',stats.var(l),stats.var(l))
print('stdev:',stats.stdev(l),stats.stdev(l))
print('sterr:',stats.sterr(l),stats.sterr(l))
print('sem:',stats.sem(l),stats.sem(l))
print('z:',stats.z(l,4),stats.z(l,4))
print('zs:')
print(stats.zs(l))
print(stats.zs(l))

print('\nTRIMMING')
print('trimboth:')
print(stats.trimboth(l,.2))
print(stats.trimboth(lf,.2))
print(stats.trimboth(l,.2))
print(stats.trimboth(lf,.2))
print('trim1:')
print(stats.trim1(l,.2))
print(stats.trim1(lf,.2))
print(stats.trim1(l,.2))
print(stats.trim1(lf,.2))

print('\nCORRELATION')
#execfile('testpairedstats.py')

l = [float(f) for f in list(range(1,21))]
ll = [l]*5

m = dyn([float(f) for f in list(range(4,24))])
m[10] = 34.

pb = dyn([0.]*9 + [1.]*11)

print('paired:')
#stats.paired(l,m)
#stats.paired(l,l)

print()
print()
print('pearsonr:')
print(stats.pearsonr(l,m))
print(stats.pearsonr(l,l))
print('spearmanr:')
print('pointbiserialr:')
print(stats.pointbiserialr(pb,l))
print(stats.pointbiserialr(pb,l))
print('kendalltau:')
print(stats.kendalltau(l,m))
print(stats.kendalltau(l,l))
print('linregress:')
print(stats.linregress(l,m))
print(stats.linregress(l,l))

print('\nINFERENTIAL')
print('ttest_1samp:')
print(stats.ttest_1samp(l,12))
print(stats.ttest_1samp(l,12))
print('ttest_ind:')
print(stats.ttest_ind(l,m))
print(stats.ttest_ind(l,l))
print('chisquare:')
print(stats.chisquare(l))
print(stats.chisquare(l))
print('ks_2samp:')
print(stats.ks_2samp(l,m))
print(stats.ks_2samp(l,l))

print('mannwhitneyu:')
print(stats.mannwhitneyu(l,m))
print(stats.mannwhitneyu(l,l))
print('ranksums:')
print(stats.ranksums(l,m))
print(stats.ranksums(l,l))
print('wilcoxont:')
print(stats.wilcoxont(l,m))
print('kruskalwallish:')
print(stats.kruskalwallish(l,m,l))
print(len(l), len(m))
print(stats.kruskalwallish(l,l,l))
print('friedmanchisquare:')
print(stats.friedmanchisquare(l,m,l))
print(stats.friedmanchisquare(l,l,l))

l = [float(x) for x in range(1,21)]
ll = [l]*5

m = [float(x) for x in range(4,24)]
m[10] = 34. 

print('\n\nF_oneway:')
print(stats.F_oneway(l,m)) 
print(stats.F_oneway(l,l))
#print 'F_value:',stats.F_value(l),stats.F_value(l)

print('\nSUPPORT')
print('sum:',stats.sum(l),stats.sum(lf),stats.sum(l),stats.sum(lf))
print('cumsum:')
print(stats.cumsum([int(x) for x in l]))
print(stats.cumsum([int(x) for x in lf]))
print('ss:',stats.ss(l),stats.ss(lf),stats.ss(l),stats.ss(lf))
print('summult:',stats.summult(l,m),stats.summult(lf,m),stats.summult(l,l),stats.summult(lf,l))
print('sumsquared:',stats.square_of_sums(l),stats.square_of_sums(lf),stats.square_of_sums(l),stats.square_of_sums(lf))
print('sumdiffsquared:',stats.sumdiffsquared(l,m),stats.sumdiffsquared(lf,m),stats.sumdiffsquared(l,l),stats.sumdiffsquared(lf,l))
print('shellsort:')
print(stats.shellsort(m))
print(stats.shellsort(l))
print('rankdata:')
print(stats.rankdata(m))
print(stats.rankdata(l))
