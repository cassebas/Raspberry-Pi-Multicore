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

df = pd.read_csv('output/20200225-array_access_random-NO_CACHE_MGMT-2core.csv')
df = df.iloc[0:50,:]
df['movingav'] = df.loc[:,'cycles'].rolling(window=3).mean()
df
#lines = df.plot.line(y='cycles')
plt.figure(figsize=[13,3])
plt.grid(True)
plt.plot(df['cycles'], label='Number of cycles')
#plt.plot(df['movingav'], label='Moving average')
plt.legend(loc=1)

# +
df1 = pd.read_csv('output/20200226-array_access_random-1core.csv')
df1 = df1.iloc[:100,:]
df1['movingav'] = df1.loc[:,'cycles'].rolling(window=20).mean()

plt.figure(figsize=[10,3])
plt.grid(True)
plt.plot(df1['movingav'], label='Moving average core1')
plt.legend(loc=1)

# +
df2 = pd.read_csv('output/20200226-array_access_random-2core.csv')
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
df3 = pd.read_csv('output/20200226-array_access_random-3core.csv')
df3 = df3.iloc[:100,:]
df3['movingav'] = df3.loc[:,'cycles'].rolling(window=20).mean()
df3_core1 = df3.loc[df3['core']==0]
df3_core1['movingav'] = df3_core1.loc[:,'cycles'].rolling(window=10).mean()
df3_core2 = df3.loc[df4['core']==1]
df3_core2['movingav'] = df3_core2.loc[:,'cycles'].rolling(window=10).mean()
df3_core3 = df3.loc[df3['core']==2]
df3_core3['movingav'] = df3_core3.loc[:,'cycles'].rolling(window=10).mean()

plt.figure(figsize=[10,3])
plt.grid(True)
plt.plot(df3_core1['movingav'], label='Moving average core1')
plt.plot(df3_core2['movingav'], label='Moving average core2')
plt.plot(df3_core3['movingav'], label='Moving average core3')
plt.legend(loc=1)

# +
df4 = pd.read_csv('output/20200228-4444-4core.csv')
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
