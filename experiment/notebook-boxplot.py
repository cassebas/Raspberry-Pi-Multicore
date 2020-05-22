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
        g = 'report/data/cyclesdata-TEST*.csv'.format(cores, bench)
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
        max = df['cycles'].max()
        med = df['cycles'].median()
        print('Filename:{} Experiment:{}  WCET is {}, which is {:1.3f} times more than the median {}.'.format(f, label, max, max/med, med))
# -

core1_bench2_1024 = pd.read_csv('report/data/cyclesdata-1CORE_BENCH2_SBDATASIZE1024KB-1core-config2-pattern0.csv', sep=' ')
core1_bench2_1024 = core1_bench2_1024.loc[core1_bench2_1024['core'] == 0]
core1_bench2_1024.boxplot(column='cycles')
max = core1_bench2_1024['cycles'].max()
med = core1_bench2_1024['cycles'].median()
print('WCET is {}, which is {:1.3f} times more than the median {}.'.format(max, max/med, med))

core1_bench2_2048 = pd.read_csv('report/data/cyclesdata-1CORE_BENCH2_SBDATASIZE2048KB-1core-config2-pattern0.csv', sep=' ')
core1_bench2_2048 = core1_bench2_2048.loc[core1_bench2_2048['core'] == 0]
core1_bench2_2048.boxplot(column='cycles')

df = pd.read_csv('output/20200122-malardalen_bsort100_1core-clearcache.csv')
df.boxplot(column='cycles') 
df.describe()
