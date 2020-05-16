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

infiles = glob.glob('output/*.csv')
infiles

# +
pmu_event_names = {
    3: 'L1D_CACHE_REFILL',
    4: 'L1D_CACHE',
    16: 'BR_MIS_PRED',
    18: 'BR_PRED',
    19: 'MEM_ACCESS',
    21: 'L1D_CACHE_WB',
    22: 'L2D_CACHE',
    23: 'L2D_CACHE_REFILL',
    24: 'L2D_CACHE_WB',
    25: 'BUS_ACCESS',
}

def event_number2name(number):
    if number in pmu_event_names.keys():
        return pmu_event_names[number]
    else:
        return ""
#print(cycles_task['cycles'].describe().apply(lambda x: format(x, 'f')))


# -

f = 'report/data/eventsdata-TEST1-4core-config4433-pattern0000.csv'
df = pd.read_csv(f, sep=' ')
df['eventname'] = df['eventtype'].apply(lambda x: int(x, 16)).apply(event_number2name)
#df = df.drop(['eventtype'], axis=1)
df_events = df.set_index(keys=['core', 'pmu'])
df_events.sort_index(inplace=True)
print(set(df_events.index.get_level_values(0)))
print(set(df_events.index.get_level_values(1)))
#df_pmu = df_events.loc[0, :]
#print(len(set(df_pmu.index.get_level_values(0))))
#df_pmu
dfe = df_events.loc[(0,4), :]
dfe = dfe.set_index(keys=['iteration'])
dfe
#dfe = df_events.loc[(1,3),:]
#dfe = dfe.set_index(keys=['iteration'])
#dfe
#dfe = df_events.loc[(1,3),:]
#dfe['eventname'].unique()[0]
#dfe['eventcount']

# +
f = 'report/data/cyclesdata-TEST1-4core-config4433-pattern0000.csv'
df = pd.read_csv(f, sep=' ')
#df['cores'] = df['core'].astype('int32')
df2 = df.set_index(keys=['label', 'cores', 'configuration', 'pattern'])
df2.sort_index(inplace=True)
df2.dropna(axis=0, how='all', inplace=True)
df2.dropna(axis=1, how='all', inplace=True)

print(set(df2.index.get_level_values(0))) # label
print(set(df2.index.get_level_values(1))) # number of cores
print(set(df2.index.get_level_values(2))) # configuration string
print(set(df2.index.get_level_values(3))) # alignment pattern string
df2

# +
df = pd.read_csv('output/test2-cycles.csv')
#df = df.iloc[:100,:]

df_core1 = df.loc[df['core']==0]
df_core1 = df_core1.set_index(['iteration'])

plt.figure(figsize=[10,5])
plt.grid(True)
plt.plot(df_core1['cycles'], label='Cycles core1')
plt.legend(loc=1)
df.configuration.unique()[0]

# +
df = pd.read_csv('example_linearcharts/cyclesdata-default-4core-config4455-dassign0123-pattern0000.csv',
                sep=' ')
df = df.iloc[:10000,:]

df_core1 = df.loc[df['core']==0]
df_core1 = df_core1.set_index(['iteration'])
df_core2 = df.loc[df['core']==1]
df_core2 = df_core2.set_index(['iteration'])
df_core3 = df.loc[df['core']==2]
df_core3 = df_core3.set_index(['iteration'])
df_core4 = df.loc[df['core']==3]
df_core4 = df_core4.set_index(keys=['iteration'])
#df_core4['movingav'] = df_core4.loc[:,'cycles'].rolling(window=5).mean()

plt.figure(figsize=[10,5])
plt.grid(True)
plt.plot(df_core1['cycles'], label='Cycles core1')
plt.plot(df_core2['cycles'], label='Cycles core2')
plt.plot(df_core3['cycles'], label='Cycles core3')
plt.plot(df_core4['cycles'], label='Cycles core4')
plt.legend(loc=1)
df.configuration.unique()[0]

# +
df1 = pd.read_csv('example_linearcharts/20200226-array_access_random-1core.csv')
df1 = df1.iloc[:100,:]
df1['movingav'] = df1.loc[:,'cycles'].rolling(window=20).mean()

plt.figure(figsize=[10,3])
plt.grid(True)
plt.plot(df1['movingav'], label='Moving average core1')
plt.legend(loc=1)

# +
df2 = pd.read_csv('example_linearcharts/20200226-array_access_random-2core.csv')
df2 = df2.iloc[:100,:]
df2['movingav'] = df2.loc[:,'cycles'].rolling(window=20).mean()
df2_core1 = df2.loc[df2['core']==0]
df2_core1['movingav'] = df2_core1.loc[:,'cycles'].rolling(window=10).mean()
df2_core2 = df2.loc[df2['core']==1]
df2_core2['movingav'] = df2_core2.loc[:,'cycles'].rolling(window=10).mean()

plt.figure(figsize=[10,3])
plt.grid(True)
plt.plot(df2_core1['movingav'], label='Moving average core1')
plt.plot(df2_core2['movingav'], label='Moving average core2')
plt.legend(loc=1)

# +
df3 = pd.read_csv('example_linearcharts/20200226-array_access_random-3core.csv')
df3 = df3.iloc[:100,:]
df3['movingav'] = df3.loc[:,'cycles'].rolling(window=5).mean()
df3_core1 = df3.loc[df3['core']==0]
df3_core1['movingav'] = df3_core1.loc[:,'cycles'].rolling(window=10).mean()
df3_core2 = df3.loc[df3['core']==1]
df3_core2['movingav'] = df3_core2.loc[:,'cycles'].rolling(window=10).mean()
df3_core3 = df3.loc[df3['core']==2]
df3_core3['movingav'] = df3_core3.loc[:,'cycles'].rolling(window=10).mean()

plt.figure(figsize=[10,3])
plt.grid(True)
plt.plot(df3_core1['movingav'], label='Moving average core1')
plt.plot(df3_core2['movingav'], label='Moving average core2')
plt.plot(df3_core3['movingav'], label='Moving average core3')
plt.legend(loc=1)
df3

# +
df4 = pd.read_csv('example_linearcharts/20200228-4444-4core.csv')
df4 = df4.iloc[:1000,:]
df4_core1 = df4.loc[df4['core']==0]
df4_core1['movingav'] = df4_core1.loc[:,'cycles'].rolling(window=100).mean()
df4_core2 = df4.loc[df4['core']==1]
df4_core2['movingav'] = df4_core2.loc[:,'cycles'].rolling(window=100).mean()
df4_core3 = df4.loc[df4['core']==2]
df4_core3['movingav'] = df4_core3.loc[:,'cycles'].rolling(window=100).mean()
df4_core4 = df4.loc[df4['core']==3]
df4_core4['movingav'] = df4_core4.loc[:,'cycles'].rolling(window=100).mean()

plt.figure(figsize=[10,3])
plt.grid(True)
plt.plot(df4_core1['movingav'], label='Moving average core1')
plt.plot(df4_core2['movingav'], label='Moving average core2')
plt.plot(df4_core3['movingav'], label='Moving average core3')
plt.plot(df4_core4['movingav'], label='Moving average core4')
plt.legend(loc=1)

# +
df4 = pd.read_csv('output/20200228-4444-4core-2.csv')
df4 = df4.iloc[:1000,:]
df4_core1 = df4.loc[df4['core']==0]
df4_core1['movingav'] = df4_core1.loc[:,'cycles'].rolling(window=100).mean()
df4_core2 = df4.loc[df4['core']==1]
df4_core2['movingav'] = df4_core2.loc[:,'cycles'].rolling(window=100).mean()
df4_core3 = df4.loc[df4['core']==2]
df4_core3['movingav'] = df4_core3.loc[:,'cycles'].rolling(window=100).mean()
df4_core4 = df4.loc[df4['core']==3]
df4_core4['movingav'] = df4_core4.loc[:,'cycles'].rolling(window=100).mean()

plt.figure(figsize=[10,3])
plt.grid(True)
plt.plot(df4_core1['movingav'], label='Moving average core1')
plt.plot(df4_core2['movingav'], label='Moving average core2')
plt.plot(df4_core3['movingav'], label='Moving average core3')
plt.plot(df4_core4['movingav'], label='Moving average core4')
plt.legend(loc=1)

# +
df2 = pd.read_csv('output/20200108-malardalen_bsort100_2core.csv')

df2_00 = df2[(df2['pattern'] == '\'00\'') & (df2['core'] == 0)].reset_index()
df2_01 = df2[(df2['pattern'] == '\'00\'') & (df2['core'] == 1)].reset_index()

df2_10 = df2[(df2['pattern'] == '\'01\'') & (df2['core'] == 0)].reset_index()
df2_11 = df2[(df2['pattern'] == '\'01\'') & (df2['core'] == 1)].reset_index()

df2_20 = df2[(df2['pattern'] == '\'02\'') & (df2['core'] == 0)].reset_index()
df2_21 = df2[(df2['pattern'] == '\'02\'') & (df2['core'] == 1)].reset_index()

fig, (ax1,ax2) = plt.subplots(1,2, figsize=(10,4))  # 1 row, 2 columns
df2_00.plot(y='cycles', ax=ax1, label='cycles core 0')
df2_01.plot(y='cycles', ax=ax2, label='cycles core 1, offset=0')
ax1.set_ylim([5200000, 5800000])
ax2.set_ylim([5200000, 5800000])
plt.tight_layout()

fig, (ax1,ax2) = plt.subplots(1,2, figsize=(10,4))  # 1 row, 2 columns
df2_10.plot(y='cycles', ax=ax1, label='cycles core 0')
df2_11.plot(y='cycles', ax=ax2, label='cycles core 1, offset=1')
ax1.set_ylim([5200000, 5800000])
ax2.set_ylim([5200000, 5800000])
plt.tight_layout()

fig, (ax1,ax2) = plt.subplots(1,2, figsize=(10,4))  # 1 row, 2 columns
df2_20.plot(y='cycles', ax=ax1, label='cycles core 0')
df2_21.plot(y='cycles', ax=ax2, label='cycles core 1, offset=2')
ax1.set_ylim([5200000, 5800000])
ax2.set_ylim([5200000, 5800000])
plt.tight_layout()
# -

df = pd.read_csv('output/20200108-malardalen_bsort100_2core.csv')
lines = df.plot.line(y='cycles')

df = pd.read_csv('output/20200108-malardalen_bsort100_3core.csv')
lines = df.plot.line(y='cycles')

df = pd.read_csv('output/20200108-malardalen_bsort100_4core.csv')
lines = df.plot.line(y='cycles')
