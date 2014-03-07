from stats import *
import pstat

def dopaired(x,y):
    """\nRuns all paired stats that are possible to run on the data provided.
Assumes 2 columns to the input data.

Format:  dopaired(x,y)
Returns: appropriate statistcs\n"""

    t,p = ttest_ind(x,y)
    print '\nAssuming 2 independent samples ...'
    print 'Independent samples t-test:  ', round(t,3),round(p,3)

    if len(x)>20 or len(y)>20:
	z,p = ranksums(x,y)
	print '\nAssuming 2 independent samples, NONPARAMETRIC, n>20 ...'
	print 'Rank Sums test:  ', round(z,3),round(p,3)
    else:
	u,p = mannwhitneyu(x,y)
	print '\nAssuming 2 independent samples, NONPARAMETRIC, ns<20 ...'
	print 'Mann-Whitney U-test:  ', round(u,3),round(p,3)

    if len(pstat.unique(x))==2:
	r,p = pointbiserialr(x,y)
	print '\nIf x contains a dichotomous variable ...'
	print 'Point Biserial r: ',round(r,3),round(p,3)

    if len(x) == len(y):
	t, p = ttest_rel(x,y)	
	print '\nAssuming 2 related samples ...'
	print 'Related samples t-test:  ', round(t,3),round(p,3)

	t, p = wilcoxont(x,y)	
	print '\nAssuming 2 related samples, NONPARAMETRIC ...'
	print 'Wilcoxon T-test:  ', round(t,3),round(p,3)

	m,b,r,p,see = linregress(x,y)
	print '\nLinear regression for continuous variables ...'
	print 'Slope,intercept,r,prob,stderr estimate: ',round(m,3),round(b,3),round(r,3),round(p,3),round(see,3)

	r,p = pearsonr(x,y)
	print '\nCorrelation for continuous variables ...'
	print "Pearson's r: ",round(r,3),round(p,3)

	r,p = spearmanr(x,y)
	print '\nCorrelation for ranked variables ...'
	print "Spearman's r: ", round(r,3), round(p,3)

