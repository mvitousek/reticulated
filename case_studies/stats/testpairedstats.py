from imp import reload

import stats
reload(stats)
import pstat
reload(pstat)
import statshelp

print('\n\nSingle Sample t-test')

x = [50.,75.,65.,72.,68.,65.,73.,59.,64.]
print('SHOULD BE ... t=-3.61, p<0.01 (df=8) ... Basic Stats 1st ed, p.307')
stats.ttest_1samp(x,75,1)


print('\n\nIndependent Samples t-test')

a = list(map(float,[11.,16.,20.,17.,10.,12.]))
b = list(map(float,[8.,11.,15.,11.,11.,12.,11.,7.]))
print('\n\nSHOULD BE ??? <p< (df=) ... ')
stats.ttest_ind(a,b,1)


print('\n\nRelated Samples t-test')

before = list(map(float,[11,16,20,17,10]))
after = list(map(float,[8,11,15,11,11]))
print('\n\nSHOULD BE t=+2.88, 0.01<p<0.05 (df=4) ... Basic Stats 1st ed, p.359')
stats.ttest_rel(before,after,1,'Before','After')


print("\n\nPearson's r")

x = list(map(float,[0,0,1,1,1,2,2,3,3,4]))
y = list(map(float,[8,7,7,6,5,4,4,4,2,0]))
print('SHOULD BE -0.94535 (N=10) ... Basic Stats 1st ed, p.190')
print(stats.pearsonr(x,y))


print("\n\nSpearman's r")

x = list(map(float,[4,1,9,8,3,5,6,2,7]))
y = list(map(float,[3,2,8,6,5,4,7,1,9]))
print('\nSHOULD BE +0.85 on the dot (N=9) ... Basic Stats 1st ed, p.193')
print(stats.spearmanr(x,y))


print('\n\nPoint-Biserial r')

gender = list(map(float,[1,1,1,1,2,2,2,2,2,2]))
score  = list(map(float,[35, 38, 41, 40, 60, 65, 65, 68, 68, 64]))
print('\nSHOULD BE +0.981257 (N=10) ... Basic Stats 1st ed, p.197')
print(stats.pointbiserialr(gender,score))


print('\n\nLinear Regression')

x = list(map(float,[1,1,2,2,2,3,3,3,4,4,4]))
y = list(map(float,[2,4,4,6,2,4,7,8,6,8,7]))
print('\nSHOULD BE 1.44, 1.47, 0.736, ???, 1.42 (N=11)... Basic Stats 1st ed, p.211-2')
print(stats.linregress(x,y))

print('\n\nChi-Square')

fo = list(map(float,[10,40]))
print('\nSHOULD BE 18.0, <<<0.01 (df=1) ... Basic Stats 1st ed. p.457')
print(stats.chisquare(fo))
print('\nSHOULD BE 5.556, 0.01<p<0.05 (df=1) ... Basic Stats 1st ed. p.460')
print(stats.chisquare(fo,[5,45]))


print('\n\nMann Whitney U')

red = list(map(float,[540,480,600,590,605]))
black = list(map(float,[760,890,1105,595,940]))
print('\nSHOULD BE 2.0, 0.01<p<0.05 (N=5,5) ... Basic Stats 1st ed, p.473-4')
print(stats.mannwhitneyu(red,black))

print('\n\nRank Sums')

#(using red and black from above)
print('\nSHOULD BE -2.19, p<0.0286 (slightly) ... Basic Stats 1st ed, p.474-5')
print(stats.ranksums(red,black))


print('\n\nWilcoxon T')

red   = list(map(float,[540,580, 600,680,430,740, 600,690,605,520]))
black = list(map(float,[760,710,1105,880,500,990,1050,640,595,520]))
print('\nSHOULD BE +3.0, 0.01<p<0.05 (N=9) ... Basic Stats 1st ed, p.477-8')
print(stats.wilcoxont(red,black))

print('\n\nKruskal-Wallis H')

short = list(map(float,[10,28,26,39,6]))
medium = list(map(float,[24,27,35,44,58]))
tall = list(map(float,[68,71,57,60,62]))
print('\nSHOULD BE 9.62, p<0.01 (slightly) (df=2) ... Basic Stats 1st ed, p.478-9')
print(stats.kruskalwallish(short,medium,tall))



print('\n\nFriedman Chi Square')

highman = list(map(float,[1,1,1,1,2,1,1,1,1,2]))
shyman = list(map(float,[2,3,2,3,1,3,2,3,3,1]))
whyman = list(map(float,[3,2,3,2,3,2,3,2,2,3]))
print('\nSHOULD BE 9.80, p<0.01 (slightly more) (df=2) ... Basic Stats 1st ed, p.481-2')
print(stats.friedmanchisquare(highman,shyman,whyman))


# TRY-EM-ALL

print('\n\nTRY-EM-ALL !!!\n')
statshelp.dopaired(red,black)

print('\n\nTRY-EM-ALL AGAIN!!!\n')
statshelp.dopaired(red+black+red, black+red+black)
