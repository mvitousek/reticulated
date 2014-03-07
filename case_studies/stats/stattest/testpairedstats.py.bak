import stats
reload(stats)
from Numeric import *
import pstat
reload(pstat)
import statshelp

print '\n\nSingle Sample t-test'

x = [50,75,65,72,68,65,73,59,64]
print 'SHOULD BE ... t=-3.61, p<0.01 (df=8) ... Basic Stats 1st ed, p.307'
stats.ttest_1samp(x,75,1)
stats.attest_1samp(array(x),75,1)


print '\n\nIndependent Samples t-test'

a = [11,16,20,17,10,12]
b = [8,11,15,11,11,12,11,7]
print '\n\nSHOULD BE ??? <p< (df=) ... '
stats.ttest_ind(a,b,1)
stats.attest_ind(array(a),array(b),0,1)


print '\n\nRelated Samples t-test'

before = [11,16,20,17,10]
after = [8,11,15,11,11]
print '\n\nSHOULD BE t=+2.88, 0.01<p<0.05 (df=4) ... Basic Stats 1st ed, p.359'
stats.ttest_rel(before,after,1,'Before','After')
stats.attest_rel(array(before),array(after),1,'Before','After')


print "\n\nPearson's r"

x = [0,0,1,1,1,2,2,3,3,4]
y = [8,7,7,6,5,4,4,4,2,0]
print 'SHOULD BE -0.94535 (N=10) ... Basic Stats 1st ed, p.190'
print stats.pearsonr(x,y)
print stats.apearsonr(array(x),array(y))


print "\n\nSpearman's r"

x = [4,1,9,8,3,5,6,2,7]
y = [3,2,8,6,5,4,7,1,9]
print '\nSHOULD BE +0.85 on the dot (N=9) ... Basic Stats 1st ed, p.193'
print stats.spearmanr(x,y)
print stats.aspearmanr(array(x),array(y))


print '\n\nPoint-Biserial r'

gender = [1,1,1,1,2,2,2,2,2,2]
score  = [35, 38, 41, 40, 60, 65, 65, 68, 68, 64]
print '\nSHOULD BE +0.981257 (N=10) ... Basic Stats 1st ed, p.197'
print stats.pointbiserialr(gender,score)
print stats.apointbiserialr(array(gender),array(score))


print '\n\nLinear Regression'

x = [1,1,2,2,2,3,3,3,4,4,4]
y = [2,4,4,6,2,4,7,8,6,8,7]
print '\nSHOULD BE 1.44, 1.47, 0.736, ???, 1.42 (N=11)... Basic Stats 1st ed, p.211-2'
print stats.linregress(x,y)
print stats.alinregress(array(x),array(y))

print '\n\nChi-Square'

fo = [10,40]
print '\nSHOULD BE 18.0, <<<0.01 (df=1) ... Basic Stats 1st ed. p.457'
print stats.chisquare(fo)
print stats.achisquare(array(fo))
print '\nSHOULD BE 5.556, 0.01<p<0.05 (df=1) ... Basic Stats 1st ed. p.460'
print stats.chisquare(fo,[5,45])
print stats.achisquare(array(fo),array([5,45],'f'))


print '\n\nMann Whitney U'

red = [540,480,600,590,605]
black = [760,890,1105,595,940]
print '\nSHOULD BE 2.0, 0.01<p<0.05 (N=5,5) ... Basic Stats 1st ed, p.473-4'
print stats.mannwhitneyu(red,black)
print stats.amannwhitneyu(array(red),array(black))

print '\n\nRank Sums'

#(using red and black from above)
print '\nSHOULD BE -2.19, p<0.0286 (slightly) ... Basic Stats 1st ed, p.474-5'
print stats.ranksums(red,black)
print stats.aranksums(N.array(red),N.array(black))


print '\n\nWilcoxon T'

red   = [540,580, 600,680,430,740, 600,690,605,520]
black = [760,710,1105,880,500,990,1050,640,595,520]
print '\nSHOULD BE +3.0, 0.01<p<0.05 (N=9) ... Basic Stats 1st ed, p.477-8'
print stats.wilcoxont(red,black)
print stats.awilcoxont(array(red),array(black))

print '\n\nKruskal-Wallis H'

short = [10,28,26,39,6]
medium = [24,27,35,44,58]
tall = [68,71,57,60,62]
print '\nSHOULD BE 9.62, p<0.01 (slightly) (df=2) ... Basic Stats 1st ed, p.478-9'
print stats.kruskalwallish(short,medium,tall)
print stats.akruskalwallish(array(short),array(medium),array(tall))



print '\n\nFriedman Chi Square'

highman = [1,1,1,1,2,1,1,1,1,2]
shyman = [2,3,2,3,1,3,2,3,3,1]
whyman = [3,2,3,2,3,2,3,2,2,3]
print '\nSHOULD BE 9.80, p<0.01 (slightly more) (df=2) ... Basic Stats 1st ed, p.481-2'
print stats.friedmanchisquare(highman,shyman,whyman)
print stats.afriedmanchisquare(array(highman),array(shyman),array(whyman))


# TRY-EM-ALL

print '\n\nTRY-EM-ALL !!!\n'
statshelp.dopaired(red,black)

print '\n\nTRY-EM-ALL AGAIN!!!\n'
statshelp.dopaired(red+black+red, black+red+black)
