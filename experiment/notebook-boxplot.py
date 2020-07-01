# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:light
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.4.0
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

import pandas as pd
import numpy as np
from scipy.stats import ttest_ind
from scipy.stats import mannwhitneyu
import matplotlib.pyplot as plt
import glob
from itertools import combinations
from itertools import combinations_with_replacement
from itertools import permutations
from itertools import product
import re

# + jupyter={"outputs_hidden": true}
g = 'report/data/*.csv'
filenames = glob.glob(g)
filenames

# +
benchmarks = ['1', '2', '3', '4', '5', '6']
flist = []
for cores in range(1, 5):
    prod = product(benchmarks, repeat=cores)
    for p in prod:
        bench = ''.join(p)
        g = 'report/data/cyclesdata-MIDTERM_*.csv'.format(cores, bench)
        filenames = glob.glob(g)
        flist += filenames

flist = list(set(flist))
flist.sort()
regex = re.compile(r'^.*cyclesdata-([^-]*).*$')
for f in flist:
    m = regex.match(f)
    if m:
        label = m.group(1)
        df = pd.read_csv(f, sep=' ')
        df = df.loc[df['core'] == 0]
        maximum = df['cycles'].max()
        median = df['cycles'].median()
        print('Filename:{} Experiment:{}  WCET is {}, which is {:1.3f} times more than the median {}.'.format(f, label, maximum, maximum/median, median))

# +
flist = []
for cores in range(1, 5):
    prod = product(benchmarks, repeat=cores)
    for p in prod:
        bench = ''.join(p)
        g = 'report/data/eventsdata-MIDTERM_*.csv'.format(cores, bench)
        filenames = glob.glob(g)
        flist += filenames

flist = list(set(flist))
flist.sort()
regex = re.compile(r'^.*eventsdata-([^-]*).*$')
for f in flist:
    m = regex.match(f)
    eventtypes=['0x13', '0x16', '0x17', '0x19']
    eventnames=['memory access', 'L2D cache access', 'L2D cache refill', 'Bus access']
    if m:
        label = m.group(1)
        df = pd.read_csv(f, sep=' ')
        df = df.loc[df['core'] == 0]
        for i in range(3,4):
            df_tmp = df.loc[df['eventtype'] == eventtypes[i]]
            maximum = df_tmp['eventcount'].max()
            median = df_tmp['eventcount'].median()
            print('Experiment:{}  Event:{} Maximum is {}, which is {:1.3f} times more than the median {}.'.format(label, eventnames[i], maximum, maximum/median, median))
# -

boxprops = dict(linestyle='-', linewidth=3, color='k')
medianprops = dict(linestyle='-', linewidth=3, color='k')
def set_boxplot_linewidth(bp, linewidth=3):
    [[item.set_linewidth(linewidth) for item in bp[key]] for key in bp.keys()]
    [[item.set_linewidth(linewidth) for item in bp[key]] for key in bp.keys()]
    [[item.set_linewidth(linewidth) for item in bp[key]] for key in bp.keys()]
    [[item.set_linewidth(linewidth) for item in bp[key]] for key in bp.keys()]
    [[item.set_linewidth(linewidth) for item in bp[key]] for key in bp.keys()]
    [[item.set_linewidth(linewidth) for item in bp[key]] for key in bp.keys()]


# +
from matplotlib import rcParams
labelsize = 32
rcParams['xtick.labelsize'] = labelsize
rcParams['ytick.labelsize'] = labelsize

bsort1_2000 = pd.read_csv('report/data/cyclesdata-BENCH1_2000-1core-config1-pattern0.csv', sep=' ')
bsort1444_2000 = pd.read_csv('report/data/cyclesdata-BENCH1444_2000-4core-config1444-pattern0000.csv', sep=' ')
fig, ax = plt.subplots(1, 2, sharey=True, figsize=(12,12))
xlab1 = ax[0].set_xlabel('run in isolation', fontsize=40, color='green')
xlab2 = ax[1].set_xlabel('with co-runners', fontsize=40, color='red')
maximum = [0, 0]
for i, df in enumerate([bsort1_2000, bsort1444_2000]):
    df = df.loc[df['core'] == 0]
    maximum[i] = df['cycles'].max()
    boxplot = df.boxplot(column=['cycles'], ax=ax[i], return_type='dict')
    set_boxplot_linewidth(boxplot, linewidth=4)

plt.savefig('/home/caspar/git/RTS-thesis/talks/midterm-20200701/img/bsort2000-boxplot.png', bbox_inches='tight')
print('The WCET of running 4 cores compared to 1 core is {} times slower'.format(maximum[1]/maximum[0]))
# -

# Calculate the Mann-Whitney U test
a = bsort1_2000['cycles']
b = bsort1444_2000.loc[bsort1444_2000['core'] == 0]['cycles']
t, p = ttest_ind(b, a, equal_var=False)
stat, p = mannwhitneyu(a, b)
alpha = 0.05
print('The calculated statistic is {}.'.format(stat))
print('The calculated p-value is {}.'.format(p))
if p < alpha:
    # enough evidence to reject H0
    print('Based on the Mann-Whitney U test with stat={} and p={}, we can reject the Null-hypothesis'.format(stat, p))
else:
    print('Based on the Mann-Whitney U test with stat={} and p={}, we cannot reject the Null-hypothesis'.format(stat, p))

# +
bsort1_6000 = pd.read_csv('report/data/cyclesdata-BENCH1_6000_STATIC-1core-config1-pattern0.csv', sep=' ')
bsort1444_6000 = pd.read_csv('report/data/cyclesdata-BENCH1444_6000_STATIC-4core-config1444-pattern0000.csv', sep=' ')
fig, ax = plt.subplots(1, 2, sharey=True, figsize=(10,10))
maximum = [0, 0]
for i, df in enumerate([bsort1_6000, bsort1444_6000]):
    df = df.loc[df['core'] == 0]
    maximum[i] = df['cycles'].max()
    boxplot = df.boxplot(column=['cycles'], ax=ax[i], return_type='dict')
    set_boxplot_linewidth(boxplot, linewidth=4)
    
print('The WCET of running 4 cores compared to 1 core is {} times slower'.format(maximum[1]/maximum[0]))
# -

# Calculate the student t-test
a = bsort1_6000['cycles']
b = bsort1444_6000.loc[bsort1444_6000['core'] == 0]['cycles']
stat, p = mannwhitneyu(a, b)
alpha = 0.05
print('The calculated statistic is {}.'.format(stat))
print('The calculated p-value is {}.'.format(p))
if p < alpha:
    # enough evidence to reject H0
    print('Based on the Mann-Whitney U test with stat={} and p={}, we can reject the Null-hypothesis'.format(stat, p))
else:
    print('Based on the Mann-Whitney U test with stat={} and p={}, we cannot reject the Null-hypothesis'.format(stat, p))

# +
from matplotlib import rcParams
labelsize = 32
rcParams['xtick.labelsize'] = labelsize
rcParams['ytick.labelsize'] = labelsize

bsort1_8000 = pd.read_csv('report/data/cyclesdata-BENCH1_8000-1core-config1-pattern0.csv', sep=' ')
bsort1444_8000 = pd.read_csv('report/data/cyclesdata-BENCH1444_8000-4core-config1444-pattern0000.csv', sep=' ')
fig, ax = plt.subplots(1, 2, sharey=True, figsize=(10,8))
xlab1 = ax[0].set_xlabel('run in isolation  ', fontsize=40, color='green')
xlab2 = ax[1].set_xlabel('   with co-runners', fontsize=40, color='red')
max = [0, 0]
for i, df in enumerate([bsort1_8000, bsort1444_8000]):
    df = df.loc[df['core'] == 0]
    max[i] = df['cycles'].max()
    boxplot = df.boxplot(column=['cycles'], ax=ax[i], return_type='dict')
    set_boxplot_linewidth(boxplot, linewidth=4)
    
plt.savefig('/home/caspar/git/RTS-thesis/talks/midterm-20200701/img/bsort8000-boxplot.png', bbox_inches='tight')
print('The WCET of running 4 cores compared to 1 core is {} times slower'.format(max[1]/max[0]))
# -

# Calculate the student t-test
a = bsort1_8000['cycles']
b = bsort1444_8000.loc[bsort1444_8000['core'] == 0]['cycles']
stat, p = mannwhitneyu(a, b)
alpha = 0.05
print('The calculated statistic is {}.'.format(stat))
print('The calculated p-value is {}.'.format(p))
if p < alpha:
    # enough evidence to reject H0
    print('Based on the Mann-Whitney U test with stat={} and p={}, we can reject the Null-hypothesis'.format(stat, p))
else:
    print('Based on the Mann-Whitney U test with stat={} and p={}, we cannot reject the Null-hypothesis'.format(stat, p))

# +
cores = range(1,5)
attacks = ['readattack linear', 'readattack random', 'writeattack linear', 'writeattack random']
disparity32lst = [
    [1, 1.011, 1.039, 1.148],
    [1, 1.025, 1.042, 1.082],
    [1, 1.131, 10.778, 21.920],
    [1, 1.151, 4.729, 11.922]]
disparity64lst = [
    [1, 1.046, 1.132, 1.402],
    [1, 1.035, 1.062, 1.120],
    [1, 1.488, 35.740, 69.578],
    [1, 1.393, 10.812, 28.931]]
disparity96lst = [
    [1, 1.084, 1.217, 1.537],
    [1, 1.056, 1.082, 1.142],
    [1, 1.794, 30.909, 47.293],
    [1, 1.562, 11.954, 30.126]]
disparity128lst = [
    [1, 1.128, 1.313, 1.710],
    [1, 1.065, 1.114, 1.189],
    [1, 2.091, 17.516, 26.530],
    [1, 1.720, 18.898, 32.189]]
disparity160lst = [
    [1, 1.145, 1.371, 1.804],
    [1, 1.056, 1.114, 1.204],
    [1, 2.224, 10.762, 16.025],
    [1, 1.819, 12.686, 19.337]]
disparity192lst = [
    [1, 1.185, 1.470, 1.913],
    [1, 1.075, 1.147, 1.259],
    [1, 2.331, 7.722, 11.266],
    [1, 1.936, 9.057, 13.540]]

disparity32 = pd.DataFrame(disparity32lst)
disparity32 = disparity32.transpose()
disparity32.index = cores
disparity32.columns = attacks

disparity64 = pd.DataFrame(disparity64lst)
disparity64 = disparity64.transpose()
disparity64.index = cores
disparity64.columns = attacks

disparity96 = pd.DataFrame(disparity96lst)
disparity96 = disparity96.transpose()
disparity96.index = cores
disparity96.columns = attacks

disparity128 = pd.DataFrame(disparity128lst)
disparity128 = disparity128.transpose()
disparity128.index = cores
disparity128.columns = attacks

disparity160 = pd.DataFrame(disparity160lst)
disparity160 = disparity160.transpose()
disparity160.index = cores
disparity160.columns = attacks

disparity192 = pd.DataFrame(disparity192lst)
disparity192 = disparity192.transpose()
disparity192.index = cores
disparity192.columns = attacks
# -

fig, ax = plt.subplots(1, 1, sharey=True, figsize=(15, 8))
ax.set_title('Disparity + linear array access', fontsize=20)
ax.set_xticks(cores)
ax.plot(disparity32[attacks[0]], label='Linear array access, disparity 32x32', marker='o')
ax.plot(disparity64[attacks[0]], label='Linear array access, disparity 64x64', marker='o')
ax.plot(disparity96[attacks[0]], label='Linear array access, disparity 96x96', marker='o')
ax.plot(disparity128[attacks[0]], label='Linear array access, disparity 128x128', marker='o')
ax.plot(disparity160[attacks[0]], label='Linear array access, disparity 160x160', marker='o')
ax.plot(disparity192[attacks[0]], label='Linear array access, disparity 192x192', marker='o')
ax.set_xlabel('Number of cores', fontsize=18)
ax.set_ylabel('Slowdown factor', fontsize=18)
ax.legend(loc=0, fontsize=14)
fig.tight_layout()
plt.savefig('/home/caspar/git/RTS-thesis/talks/midterm-20200701/img/disparity-lineararrayaccess.png')

fig, ax = plt.subplots(1, 1, sharey=True, figsize=(15, 8))
ax.set_xticks(cores)
ax.set_title('Disparity + random array access', fontsize=20)
ax.plot(disparity32[attacks[1]], label='Random array access, disparity 32x32', marker='o')
ax.plot(disparity64[attacks[1]], label='Random array access, disparity 64x64', marker='o')
ax.plot(disparity96[attacks[1]], label='Random array access, disparity 96x96', marker='o')
ax.plot(disparity128[attacks[1]], label='Random array access, disparity 128x128', marker='o')
ax.plot(disparity160[attacks[1]], label='Random array access, disparity 160x160', marker='o')
ax.plot(disparity192[attacks[1]], label='Random array access, disparity 192x192', marker='o')
ax.set_xlabel('Number of cores', fontsize=18)
ax.set_ylabel('Slowdown factor', fontsize=18)
ax.legend(loc=0, fontsize=14)
fig.tight_layout()
plt.savefig('/home/caspar/git/RTS-thesis/talks/midterm-20200701/img/disparity-randomarrayaccess.png')

fig, ax = plt.subplots(1, 1, sharey=True, figsize=(15, 8))
ax.set_xticks(cores)
ax.set_title('Disparity + linear array write', fontsize=20)
ax.plot(disparity32[attacks[2]], label='Linear array write, disparity 32x32', marker='o')
ax.plot(disparity64[attacks[2]], label='Linear array write, disparity 64x64', marker='o')
ax.plot(disparity96[attacks[2]], label='Linear array write, disparity 96x96', marker='o')
ax.plot(disparity128[attacks[2]], label='Linear array write, disparity 128x128', marker='o')
ax.plot(disparity160[attacks[2]], label='Linear array write, disparity 160x160', marker='o')
ax.plot(disparity192[attacks[2]], label='Linear array write, disparity 192x192', marker='o')
ax.set_xlabel('Number of cores', fontsize=18)
ax.set_ylabel('Slowdown factor', fontsize=18)
ax.legend(loc=0, fontsize=14)
fig.tight_layout()
plt.savefig('/home/caspar/git/RTS-thesis/talks/midterm-20200701/img/disparity-lineararraywrite.png')

fig, ax = plt.subplots(1, 1, sharey=True, figsize=(15, 8))
ax.set_xticks(cores)
ax.set_title('Disparity + random array write', fontsize=20)
ax.plot(disparity32[attacks[3]], label='Random array write, disparity 32x32', marker='o')
ax.plot(disparity64[attacks[3]], label='Random array write, disparity 64x64', marker='o')
ax.plot(disparity96[attacks[3]], label='Random array write, disparity 96x96', marker='o')
ax.plot(disparity128[attacks[3]], label='Random array write, disparity 128x128', marker='o')
ax.plot(disparity160[attacks[3]], label='Random array write, disparity 160x160', marker='o')
ax.plot(disparity192[attacks[3]], label='Random array write, disparity 192x192', marker='o')
ax.set_xlabel('Number of cores', fontsize=18)
ax.set_ylabel('Slowdown factor', fontsize=18)
ax.legend(loc=0, fontsize=14)
plt.savefig('disparity-randomarraywrite')
plt.savefig('/home/caspar/git/RTS-thesis/talks/midterm-20200701/img/disparity-randomarraywrite.png')

mem_sizes = ['32x32', '64x64', '96x96', '128x128', '160x160', '192x192']
slow_down = []
for i in range(4):
    slow_down.append([disparity32.loc[4, attacks[i]],
                      disparity64.loc[4, attacks[i]],
                      disparity96.loc[4, attacks[i]],
                      disparity128.loc[4, attacks[i]],
                      disparity160.loc[4, attacks[i]],
                      disparity192.loc[4, attacks[i]]])

fig, ax = plt.subplots(1, 1, sharey=True, figsize=(10, 5))
ax.set_xlabel('Input size', fontsize=18)
ax.set_ylabel('Slowdown factor', fontsize=18)
ax.bar(mem_sizes, slow_down[0], align='center', alpha=0.5, width=0.75)
ax.set_title('Disparity: Linear read attack on 4 cores', fontsize=20)
ax.set_xticks(mem_sizes)
ax.tick_params(labelrotation=45)

fig, ax = plt.subplots(1, 1, sharey=True, figsize=(10, 5))
ax.set_xlabel('Input size', fontsize=18)
ax.set_ylabel('Slowdown factor', fontsize=18)
ax.bar(mem_sizes, slow_down[1], align='center', alpha=0.5, width=0.75)
ax.set_title('Disparity: Random read attack on 4 cores', fontsize=20)
ax.set_xticks(mem_sizes)
ax.tick_params(labelrotation=45)

fig, ax = plt.subplots(1, 1, sharey=True, figsize=(10, 5))
ax.set_xlabel('Input size', fontsize=18)
ax.set_ylabel('Slowdown factor', fontsize=18)
ax.bar(mem_sizes, slow_down[2], align='center', alpha=0.5, width=0.75)
ax.set_title('Disparity: Linear write attack on 4 cores', fontsize=20)
ax.set_xticks(mem_sizes)
ax.tick_params(labelrotation=45)

fig, ax = plt.subplots(1, 1, sharey=True, figsize=(10, 5))
ax.set_xlabel('Input size', fontsize=18)
ax.set_ylabel('Slowdown factor', fontsize=18)
ax.bar(mem_sizes, slow_down[3], align='center', alpha=0.5, width=0.75)
ax.set_title('Disparity: Random write attack on 4 cores', fontsize=20)
ax.set_xticks(mem_sizes)
ax.tick_params(labelrotation=45)


# +
def autolabel(ax, bars):
    """Attach a text label above each bar in *rects*, displaying its height."""
    for bar in bars:
        height = bar.get_height()
        ax.annotate('{:.3}'.format(height),
                    xy=(bar.get_x() + bar.get_width() / 3, height),
                    xytext=(5, 5),  # 3 points vertical offset
                    textcoords="offset points",
                    ha='center', va='bottom',
                    fontsize=20)

mem_sizes = ['32x32', '64x64', '96x96', '128x128', '160x160', '192x192']
index = np.arange(len(mem_sizes))
y_ticks = [1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 2.0]
width = 0.3
# -

fig, ax = plt.subplots(1, 1, sharey=True, figsize=(15,6))
slowdown = []
for i in range(2, 5):
    slowdown.append([disparity32.loc[i, attacks[0]],
                     disparity64.loc[i, attacks[0]],
                     disparity96.loc[i, attacks[0]],
                     disparity128.loc[i, attacks[0]],
                     disparity160.loc[i, attacks[0]],
                     disparity192.loc[i, attacks[0]]])
bars1 = ax.bar(index - width, slowdown[0], width, label='2 cores')
bars2 = ax.bar(index, slowdown[1], width, label='3 cores')
bars3 = ax.bar(index + width, slowdown[2], width, label='4 cores')
ax.legend(fontsize=14)
ax.set_title('Disparity + Linear array access co-runners', fontsize=20)
ax.set_xlabel('Input size', fontsize=18)
ax.set_ylabel('Slowdown factor', fontsize=18)
ax.set_xticks(index)
ax.set_ylim([1.0, 2.0])
ax.set_xticklabels(mem_sizes, fontsize=14)
ax.tick_params(labelrotation=45)
autolabel(ax, bars1)
autolabel(ax, bars2)
autolabel(ax, bars3)
fig.tight_layout()
plt.savefig('/home/caspar/git/RTS-thesis/talks/midterm-20200701/img/disparity-lineararrayaccess-bars.png')

fig, ax = plt.subplots(1, 1, sharey=True, figsize=(15,6))
slowdown = []
for i in range(2, 5):
    slowdown.append([disparity32.loc[i, attacks[1]],
                     disparity64.loc[i, attacks[1]],
                     disparity96.loc[i, attacks[1]],
                     disparity128.loc[i, attacks[1]],
                     disparity160.loc[i, attacks[1]],
                     disparity192.loc[i, attacks[1]]])
bars1 = ax.bar(index - width, slowdown[0], width, label='2 cores')
bars2 = ax.bar(index, slowdown[1], width, label='3 cores')
bars3 = ax.bar(index + width, slowdown[2], width, label='4 cores')
ax.legend(fontsize=14)
ax.set_title('Disparity + Random array access co-runners', fontsize=20)
ax.set_xlabel('Input size', fontsize=18)
ax.set_ylabel('Slowdown factor', fontsize=18)
ax.set_xticks(index)
ax.set_ylim([1.0, 2.0])
ax.set_xticklabels(mem_sizes, fontsize=14)
ax.tick_params(labelrotation=45)
autolabel(ax, bars1)
autolabel(ax, bars2)
autolabel(ax, bars3)
fig.tight_layout()
plt.savefig('/home/caspar/git/RTS-thesis/talks/midterm-20200701/img/disparity-randomarrayaccess-bars.png')

mem_sizes = ['32x32', '64x64', '96x96', '128x128', '160x160', '192x192']
index = np.arange(len(mem_sizes))
width = 0.3

fig, ax = plt.subplots(1, 1, sharey=True, figsize=(15,8))
slowdown = []
for i in range(2, 5):
    slowdown.append([disparity32.loc[i, attacks[2]],
                     disparity64.loc[i, attacks[2]],
                     disparity96.loc[i, attacks[2]],
                     disparity128.loc[i, attacks[2]],
                     disparity160.loc[i, attacks[2]],
                     disparity192.loc[i, attacks[2]]])
bars1 = ax.bar(index - width, slowdown[0], width, label='2 cores: 1 task, 1 co-runner')
bars2 = ax.bar(index, slowdown[1], width, label='3 cores: 1 task, 2 co-runners')
bars3 = ax.bar(index + width, slowdown[2], width, label='4 cores: 1 task, 3 co-runners')
ax.legend(fontsize=20)
ax.set_title('Disparity + Linear array write co-runners', fontsize=28)
ax.set_xlabel('Input size', fontsize=28)
ax.set_ylabel('Slowdown factor', fontsize=24)
ax.set_ylim([1.0, 75.0])
ax.set_xticks(index)
ax.set_xticklabels(mem_sizes, fontsize=22)
ax.tick_params(labelrotation=45)
autolabel(ax, bars1)
autolabel(ax, bars2)
autolabel(ax, bars3)
fig.tight_layout()
plt.savefig('/home/caspar/git/RTS-thesis/talks/midterm-20200701/img/disparity-lineararraywrite-bars.png')

fig, ax = plt.subplots(1, 1, sharey=True, figsize=(15,6))
slowdown = []
for i in range(2, 5):
    slowdown.append([disparity32.loc[i, attacks[3]],
                     disparity64.loc[i, attacks[3]],
                     disparity96.loc[i, attacks[3]],
                     disparity128.loc[i, attacks[3]],
                     disparity160.loc[i, attacks[3]],
                     disparity192.loc[i, attacks[3]]])
bars1 = ax.bar(index - width, slowdown[0], width, label='2 cores')
bars2 = ax.bar(index, slowdown[1], width, label='3 cores')
bars3 = ax.bar(index + width, slowdown[2], width, label='4 cores')
ax.legend(fontsize=14)
ax.set_title('Disparity + Random array write co-runners', fontsize=20)
ax.set_xlabel('Input size', fontsize=18)
ax.set_ylabel('Slowdown factor', fontsize=18)
ax.set_ylim([1.0, 75.0])
ax.set_xticks(index)
ax.set_xticklabels(mem_sizes, fontsize=14)
ax.tick_params(labelrotation=45)
autolabel(ax, bars1)
autolabel(ax, bars2)
autolabel(ax, bars3)
fig.tight_layout()
plt.savefig('/home/caspar/git/RTS-thesis/talks/midterm-20200701/img/disparity-randomarraywrite-bars.png')

mem_sizes = ['32x32', '64x64', '96x96', '128x128', '160x160', '192x192']
index = np.arange(len(mem_sizes))
width = 0.4

# +
fig, ax = plt.subplots(figsize=(12,8))
slowdown = []
for i in range(2, 4):
    slowdown.append([disparity32.loc[2, attacks[i]],
                     disparity64.loc[2, attacks[i]],
                     disparity96.loc[2, attacks[i]],
                     disparity128.loc[2, attacks[i]],
                     disparity160.loc[2, attacks[i]],
                     disparity192.loc[2, attacks[i]]])
bars1 = ax.bar(index - width, slowdown[0], width, label='Linear write attack')
bars2 = ax.bar(index, slowdown[1], width, label='Random write attack')

ax.legend()
ax.set_title('Write attack - 2 cores')
ax.set_xlabel('Input size')
ax.set_ylabel('Slowdown factor')
ax.set_xticks(index)
ax.set_xticklabels(mem_sizes)
ax.tick_params(labelrotation=45)
autolabel(ax, bars1)
autolabel(ax, bars2)

# +
fig, ax = plt.subplots(figsize=(12,8))
slowdown = []
for i in range(2, 4):
    slowdown.append([disparity32.loc[3, attacks[i]],
                     disparity64.loc[3, attacks[i]],
                     disparity96.loc[3, attacks[i]],
                     disparity128.loc[3, attacks[i]],
                     disparity160.loc[3, attacks[i]],
                     disparity192.loc[3, attacks[i]]])
bars1 = ax.bar(index - width, slowdown[0], width, label='Linear write attack')
bars2 = ax.bar(index, slowdown[1], width, label='Random write attack')

ax.legend()
ax.set_title('Write attack - 3 cores')
ax.set_xlabel('Input size')
ax.set_xticks(index)
ax.set_xticklabels(mem_sizes)
ax.tick_params(labelrotation=45)
autolabel(ax, bars1)
autolabel(ax, bars2)

# +
fig, ax = plt.subplots(figsize=(12,8))
slowdown = []
for i in range(2, 4):
    slowdown.append([disparity32.loc[4, attacks[i]],
                     disparity64.loc[4, attacks[i]],
                     disparity96.loc[4, attacks[i]],
                     disparity128.loc[4, attacks[i]],
                     disparity160.loc[4, attacks[i]],
                     disparity192.loc[4, attacks[i]]])
bars1 = ax.bar(index - width, slowdown[0], width, label='Linear write attack')
bars2 = ax.bar(index, slowdown[1], width, label='Random write attack')

ax.legend()
ax.set_title('Write attack - 4 cores')
ax.set_xlabel('Input size')
ax.set_xticks(index)
ax.set_xticklabels(mem_sizes)
ax.tick_params(labelrotation=45)
autolabel(ax, bars1)
autolabel(ax, bars2)


fig.suptitle('Disparity benchmark Write attacks')
fig.tight_layout(rect=[0, 0.03, 1, 0.95])
