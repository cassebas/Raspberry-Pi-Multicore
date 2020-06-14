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
import matplotlib.pyplot as plt
import glob
from itertools import combinations
from itertools import combinations_with_replacement
from itertools import permutations
from itertools import product
import re

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
        g = 'report/data/cyclesdata-BENCH1*_6000*.csv'.format(cores, bench)
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
bsort1_2000 = pd.read_csv('report/data/cyclesdata-BENCH1_2000-1core-config1-pattern0.csv', sep=' ')
bsort1444_2000 = pd.read_csv('report/data/cyclesdata-BENCH1444_2000-4core-config1444-pattern0000.csv', sep=' ')
fig, ax = plt.subplots(1, 2, sharey=True, figsize=(10,10))
maximum = [0, 0]
for i, df in enumerate([bsort1_2000, bsort1444_2000]):
    df = df.loc[df['core'] == 0]
    maximum[i] = df['cycles'].max()
    boxplot = df.boxplot(column=['cycles'], ax=ax[i], return_type='dict')
    set_boxplot_linewidth(boxplot, linewidth=4)
    
print('The WCET of running 4 cores compared to 1 core is {} times slower'.format(maximum[1]/maximum[0]))
# -

# Calculate the student t-test
a = bsort1_2000['cycles']
b = bsort1444_2000.loc[bsort1444_2000['core'] == 0]['cycles']
t, p = ttest_ind(b, a, equal_var=False)
print('The calculated t-statistic is {}.'.format(t))
print('The calculated p-value is {}.'.format(p))
print('p/2 is smaller than 0.05 is {}'.format(p/2 < 0.05))
print('t is greater than 0 is {}'.format(t > 0))
if t > 0 and p/2 < 0.05:
    # enough evidence to reject H0
    print('Based on the t-test with t={} and p={}, we can reject the Null-hypothesis'.format(t, p))
else:
    print('Based on the t-test with t={} and p={}, we cannot reject the Null-hypothesis'.format(t, p))

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
t, p = ttest_ind(b, a, equal_var=False)
print('The calculated t-statistic is {}.'.format(t))
print('The calculated p-value is {}.'.format(p))
print('p/2 is smaller than 0.05 is {}'.format(p/2 < 0.05))
print('t is greater than 0 is {}'.format(t > 0))
if t > 0 and p/2 < 0.05:
    # enough evidence to reject H0
    print('Based on the t-test with t={} and p={}, we can reject the Null-hypothesis'.format(t, p))
else:
    print('Based on the t-test with t={} and p={}, we cannot reject the Null-hypothesis'.format(t, p))

# +
bsort1_8000 = pd.read_csv('report/data/cyclesdata-BENCH1_8000-1core-config1-pattern0.csv', sep=' ')
bsort1444_8000 = pd.read_csv('report/data/cyclesdata-BENCH1444_8000-4core-config1444-pattern0000.csv', sep=' ')
fig, ax = plt.subplots(1, 2, sharey=True, figsize=(10,8))
max = [0, 0]
for i, df in enumerate([bsort1_8000, bsort1444_8000]):
    df = df.loc[df['core'] == 0]
    max[i] = df['cycles'].max()
    boxplot = df.boxplot(column=['cycles'], ax=ax[i], return_type='dict')
    set_boxplot_linewidth(boxplot, linewidth=4)
    
print('The WCET of running 4 cores compared to 1 core is {} times slower'.format(max[1]/max[0]))
# -

# Calculate the student t-test
a = bsort1_8000['cycles']
b = bsort1444_8000.loc[bsort1444_8000['core'] == 0]['cycles']
t, p = ttest_ind(b, a, equal_var=False)
print('The calculated t-statistic is {}.'.format(t))
print('The calculated p-value is {}.'.format(p))
print('p/2 is smaller than 0.05 is {}'.format(p/2 < 0.05))
print('t is greater than 0 is {}'.format(t > 0))
if t > 0 and p/2 < 0.05:
    # enough evidence to reject H0
    print('Based on the t-test with t={} and p={}, we can reject the Null-hypothesis'.format(t, p))
else:
    print('Based on the t-test with t={} and p={}, we cannot reject the Null-hypothesis'.format(t, p))

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

# +
fig, ax = plt.subplots(1, 2, sharey=True, figsize=(20, 6))
ax[0].set_xticks(cores)
ax[0].plot(disparity32[attacks[0]], label='Linear read attack, disparity 32x32', marker='o')
ax[0].plot(disparity64[attacks[0]], label='Linear read attack, disparity 64x64', marker='o')
ax[0].plot(disparity96[attacks[0]], label='Linear read attack, disparity 96x96', marker='o')
ax[0].plot(disparity128[attacks[0]], label='Linear read attack, disparity 128x128', marker='o')
ax[0].plot(disparity160[attacks[0]], label='Linear read attack, disparity 160x160', marker='o')
ax[0].plot(disparity192[attacks[0]], label='Linear read attack, disparity 192x192', marker='o')
ax[0].legend(loc=0)

ax[1].set_xticks(cores)
ax[1].plot(disparity32[attacks[1]], label='Linear read attack linear, disparity 32x32', marker='o')
ax[1].plot(disparity64[attacks[1]], label='Linear read attack linear, disparity 64x64', marker='o')
ax[1].plot(disparity96[attacks[1]], label='Linear read attack linear, disparity 96x96', marker='o')
ax[1].plot(disparity128[attacks[1]], label='Linear read attack linear, disparity 128x128', marker='o')
ax[1].plot(disparity160[attacks[1]], label='Linear read attack linear, disparity 160x160', marker='o')
ax[1].plot(disparity192[attacks[1]], label='Linear read attack linear, disparity 192x192', marker='o')
ax[1].legend(loc=0)

# +
fig, ax = plt.subplots(1, 2, sharey=True, figsize=(20, 6))
ax[0].set_xticks(cores)
ax[0].plot(disparity32[attacks[2]], label='Linear write attack, disparity 32x32', marker='o')
ax[0].plot(disparity64[attacks[2]], label='Linear write attack, disparity 64x64', marker='o')
ax[0].plot(disparity96[attacks[2]], label='Linear write attack, disparity 96x96', marker='o')
ax[0].plot(disparity128[attacks[2]], label='Linear write attack, disparity 128x128', marker='o')
ax[0].plot(disparity160[attacks[2]], label='Linear write attack, disparity 160x160', marker='o')
ax[0].plot(disparity192[attacks[2]], label='Linear write attack, disparity 192x192', marker='o')
ax[0].legend(loc=0)

ax[1].set_xticks(cores)
ax[1].plot(disparity32[attacks[3]], label='Random write attack, disparity 32x32', marker='o')
ax[1].plot(disparity64[attacks[3]], label='Random write attack, disparity 64x64', marker='o')
ax[1].plot(disparity96[attacks[3]], label='Random write attack, disparity 96x96', marker='o')
ax[1].plot(disparity128[attacks[3]], label='Random write attack, disparity 128x128', marker='o')
ax[1].plot(disparity160[attacks[3]], label='Random write attack, disparity 160x160', marker='o')
ax[1].plot(disparity192[attacks[3]], label='Random write attack, disparity 192x192', marker='o')
ax[1].legend(loc=0)

# +
mem_sizes = ['32x32', '64x64', '96x96', '128x128', '160x160', '192x192']
slow_down = []
for i in range(4):
    slow_down.append([disparity32.loc[4, attacks[i]],
                      disparity64.loc[4, attacks[i]],
                      disparity96.loc[4, attacks[i]],
                      disparity128.loc[4, attacks[i]],
                      disparity160.loc[4, attacks[i]],
                      disparity192.loc[4, attacks[i]]])

index = np.arange(len(mem_sizes))
fig, ax = plt.subplots(2, 2, sharey=True, figsize=(12, 10))

left = 0.145   # the left side of the subplots of the figure
right = 0.92   # the right side of the subplots of the figure
bottom = 0.2   # the bottom of the subplots of the figure
top = 0.9      # the top of the subplots of the figure
wspace = 0.3   # the amount of width reserved for space between subplots,
               # expressed as a fraction of the average axis width
hspace = 0.3   # the amount of height reserved for space between subplots,
               # expressed as a fraction of the average axis height
fig.subplots_adjust(left=left, right=right, bottom=bottom, top=top,
                    wspace=wspace, hspace=hspace)
fig.suptitle('Disparity attacks with MMU enabled')
ax[0, 0].set_xlabel('Input size')
ax[0, 0].set_ylabel('Slowdown factor')
ax[0, 0].bar(mem_sizes, slow_down[0], align='center', alpha=0.5, width=0.75)
ax[0, 0].set_title('Disparity: Linear read attack on 4 cores')
ax[0, 0].set_xticks(mem_sizes)
ax[0, 0].tick_params(labelrotation=45)

ax[0, 1].set_xlabel('Input size')
ax[0, 1].set_ylabel('Slowdown factor')
ax[0, 1].bar(mem_sizes, slow_down[1], align='center', alpha=0.5, width=0.75)
ax[0, 1].set_title('Disparity: Random read attack on 4 cores')
ax[0, 1].set_xticks(mem_sizes)
ax[0, 1].tick_params(labelrotation=45)

ax[1, 0].set_xlabel('Input size')
ax[1, 0].set_ylabel('Slowdown factor')
ax[1, 0].bar(mem_sizes, slow_down[2], align='center', alpha=0.5, width=0.75)
ax[1, 0].set_title('Disparity: Linear write attack on 4 cores')
ax[1, 0].set_xticks(mem_sizes)
ax[1, 0].tick_params(labelrotation=45)

ax[1, 1].set_xlabel('Input size')
ax[1, 1].set_ylabel('Slowdown factor')
ax[1, 1].bar(mem_sizes, slow_down[3], align='center', alpha=0.5, width=0.75)
ax[1, 1].set_title('Disparity: Random write attack on 4 cores')
ax[1, 1].set_xticks(mem_sizes)
ax[1, 1].tick_params(labelrotation=45)


# +
def autolabel(ax, bars):
    """Attach a text label above each bar in *rects*, displaying its height."""
    for bar in bars:
        height = bar.get_height()
        ax.annotate('{:.3}'.format(height),
                    xy=(bar.get_x() + bar.get_width() / 3, height),
                    xytext=(5, 5),  # 3 points vertical offset
                    textcoords="offset points",
                    ha='center', va='bottom')

mem_sizes = ['32x32', '64x64', '96x96', '128x128', '160x160', '192x192']
index = np.arange(len(mem_sizes))
y_ticks = [1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 2.0]
width = 0.3
fig, ax = plt.subplots(1, 2, sharey=True, figsize=(15,5))
slowdown = []
for i in range(2, 5):
    slowdown.append([disparity32.loc[i, attacks[0]],
                     disparity64.loc[i, attacks[0]],
                     disparity96.loc[i, attacks[0]],
                     disparity128.loc[i, attacks[0]],
                     disparity160.loc[i, attacks[0]],
                     disparity192.loc[i, attacks[0]]])
bars1 = ax[0].bar(index - width, slowdown[0], width, label='2 cores')
bars2 = ax[0].bar(index, slowdown[1], width, label='3 cores')
bars3 = ax[0].bar(index + width, slowdown[2], width, label='4 cores')
ax[0].legend()
ax[0].set_title('Linear read attack')
ax[0].set_xlabel('Input size')
ax[0].set_ylabel('Slowdown factor')
ax[0].set_xticks(index)
#ax[0].set_yticks(y_ticks)
ax[1].set_ylim([1.0, 2.0])
ax[0].set_xticklabels(mem_sizes)
ax[0].tick_params(labelrotation=45)
autolabel(ax[0], bars1)
autolabel(ax[0], bars2)
autolabel(ax[0], bars3)

slowdown = []
for i in range(2, 5):
    slowdown.append([disparity32.loc[i, attacks[1]],
                     disparity64.loc[i, attacks[1]],
                     disparity96.loc[i, attacks[1]],
                     disparity128.loc[i, attacks[1]],
                     disparity160.loc[i, attacks[1]],
                     disparity192.loc[i, attacks[1]]])
bars1 = ax[1].bar(index - width, slowdown[0], width, label='2 cores')
bars2 = ax[1].bar(index, slowdown[1], width, label='3 cores')
bars3 = ax[1].bar(index + width, slowdown[2], width, label='4 cores')
ax[1].legend()
ax[1].set_title('Random read attack')
ax[1].set_xlabel('Input size')
ax[1].set_xticks(index)
ax[1].set_ylim([1.0, 2.0])
ax[1].set_xticklabels(mem_sizes)
ax[1].tick_params(labelrotation=45)
autolabel(ax[1], bars1)
autolabel(ax[1], bars2)
autolabel(ax[1], bars3)



fig.suptitle('Disparity benchmark Write attacks')
fig.tight_layout()

# +
mem_sizes = ['32x32', '64x64', '96x96', '128x128', '160x160', '192x192']
index = np.arange(len(mem_sizes))
width = 0.3
fig, ax = plt.subplots(1, 2, sharey=True, figsize=(15,6))
slowdown = []
for i in range(2, 5):
    slowdown.append([disparity32.loc[i, attacks[2]],
                     disparity64.loc[i, attacks[2]],
                     disparity96.loc[i, attacks[2]],
                     disparity128.loc[i, attacks[2]],
                     disparity160.loc[i, attacks[2]],
                     disparity192.loc[i, attacks[2]]])
bars1 = ax[0].bar(index - width, slowdown[0], width, label='2 cores')
bars2 = ax[0].bar(index, slowdown[1], width, label='3 cores')
bars3 = ax[0].bar(index + width, slowdown[2], width, label='4 cores')
ax[0].legend()
ax[0].set_title('Linear write attack')
ax[0].set_xlabel('Input size')
ax[0].set_ylabel('Slowdown factor')
ax[0].set_xticks(index)
ax[0].set_xticklabels(mem_sizes)
ax[0].tick_params(labelrotation=45)
autolabel(ax[0], bars1)
autolabel(ax[0], bars2)
autolabel(ax[0], bars3)

slowdown = []
for i in range(2, 5):
    slowdown.append([disparity32.loc[i, attacks[3]],
                     disparity64.loc[i, attacks[3]],
                     disparity96.loc[i, attacks[3]],
                     disparity128.loc[i, attacks[3]],
                     disparity160.loc[i, attacks[3]],
                     disparity192.loc[i, attacks[3]]])
bars1 = ax[1].bar(index - width, slowdown[0], width, label='2 cores')
bars2 = ax[1].bar(index, slowdown[1], width, label='3 cores')
bars3 = ax[1].bar(index + width, slowdown[2], width, label='4 cores')
ax[1].legend()
ax[1].set_title('Random write attack')
ax[1].set_xlabel('Input size')
ax[1].set_xticks(index)
ax[1].set_xticklabels(mem_sizes)
ax[1].tick_params(labelrotation=45)
autolabel(ax[1], bars1)
autolabel(ax[1], bars2)
autolabel(ax[1], bars3)

fig.suptitle('Disparity benchmark Write attacks')
fig.tight_layout()
# -

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
