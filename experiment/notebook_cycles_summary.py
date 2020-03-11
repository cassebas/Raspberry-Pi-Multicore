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

pvs = pd.DataFrame()
for f in infiles:
    df = pd.read_csv(f)
    pv = pd.pivot_table(df,
                        index=['cores', 'configuration', 'dassign', 'pattern'],
                        columns=['benchmark', 'core'],
                        values='cycles',
                        aggfunc={'cycles': [np.median, np.std]})
    pv = pv.rename(columns={0: 'core0',
                            1: 'core1',
                            2: 'core2',
                            3: 'core3'})
    pvs = pd.concat([pvs, pv])
pvs.sort_index(inplace=True)
pvs.index.get_level_values(3)
pvs

benchmarks = ['malardalenbsort100',
              'lineararrayaccess',
              'syntheticbench1',
              'randomarrayaccess']
pvs_cb = pvs.loc[2, (slice(None), benchmarks, ['core0', 'core1'])]
print('malardalenbsort100' in pvs_cb.columns.get_level_values(1))
print('syntheticbench1' in pvs_cb.columns.get_level_values(1))
#pvs_cb
#pvs_tmp = pvs_cb.loc[:, (slice(None), benchmarks[2], ['core0', 'core1'])].dropna(how='all')
#pvs_tmp

pvs1 = pvs.loc[1, (slice(None), 'randomarrayaccess', 'core0')]
pvs1.dropna(how='all', inplace=True)
pvs1

pvs1.columns = pvs1.columns.to_series().str.join('-')
pvs1

pvs2 = pvs.loc[2, (slice(None), 'lineararrayaccess', ['core0', 'core1'])].dropna(how='any')
pvs2.columns = pvs2.columns.to_series().str.join('-')
pvs2

pvs3 = pvs.loc[3, (slice(None), 'lineararrayaccess', ['core0', 'core1', 'core2'])]
pvs3.dropna(how='any', inplace=True)
pvs3

pvs4 = pvs.loc[4, (slice(None), 'lineararrayaccess', slice(None))]
pvs4.dropna(how='any', inplace=True)
pvs4

pvs2_0 = pvs.loc[2, (slice(None), ['lineararrayaccess','malardalenbsort100'], ['core0', 'core1'])]
pvs2_0.dropna(how='all', inplace=True)
pvs2_0

pvs2_1 = pvs2_0.loc[:, (slice(None), ['lineararrayaccess'], ['core0', 'core1'])].dropna(how='all')
pvs2_1 = pvs2_1[pvs2_1.isnull().any(1)]
pvs2_1 = pvs2_1.loc[:, (slice(None), 'lineararrayaccess', 'core1')]
pvs2_1

pvs2_2 = pvs2_0.loc[:, (slice(None), ['malardalenbsort100'], ['core0', 'core1'])].dropna(how='all')
pvs2_2 = pvs2_2[pvs2_2.isnull().any(1)]
pvs2_2 = pvs2_2.loc[:, (slice(None), 'malardalenbsort100', 'core0')]
pvs2_2

pvs_merge = pd.merge(pvs2_1, pvs2_2, left_index=True, right_index=True)
pvs_merge

# +
pvs2_0 = pvs.loc[2, (slice(None), ['lineararrayaccess','malardalenbsort100'], ['core0', 'core1'])]
pvs2_0.dropna(how='all', inplace=True)

pvs2_3 = pvs2_0.loc[:, (slice(None), 'lineararrayaccess', ['core0', 'core1'])].dropna(how='all')
pvs2_3 = pvs2_3[pvs2_3.isnull().any(1)]
pvs2_3 = pvs2_3.loc[:, (slice(None), 'lineararrayaccess', 'core1')]
print(len(pvs2_3.index))

pvs2_4 = pvs2_0.loc[:, (slice(None), 'malardalenbsort100', ['core0', 'core1'])].dropna(how='all')
pvs2_4 = pvs2_4[pvs2_4.isnull().any(1)]
pvs2_4 = pvs2_4.loc[:, (slice(None), 'malardalenbsort100', 'core0')]
print(len(pvs2_4.index))

pvs_merge = pd.merge(pvs2_3, pvs2_4, left_index=True, right_index=True).dropna(how='any')
if len(pvs_merge.index) > 0:
    print(True)
else:
    print(False)
print(pvs2_3)
# -

pvstmp = pvs.loc[3, (slice(None), ['lineararrayaccess','malardalenbsort100'], ['core0', 'core1', 'core2'])]
pvstmp1 = pvstmp.loc[:, (slice(None), 'lineararrayaccess', ['core0', 'core1', 'core2'])].dropna(how='all')
#pvstmp = pvstmp[pvstmp.isnull().any(1)]
pvstmp1

print(pvs2_3.columns)
print(pvs2_3.index)

pv1 = pd.read_csv('report/data/cycles-2core-malardalenbsort100-lineararrayaccess.csv', sep=' ')
pv1

pv2 = pd.read_csv('report/data/cycles-2core-malardalenbsort100-lineararrayaccess.csv2', sep=' ')
pv2

pv3 = pd.read_csv('report/data/cycles-3core-malardalenbsort100-lineararrayaccess-malardalenbsort100.csv', sep=' ')
pv3

pv4 = pd.read_csv('report/data/cycles-3core-malardalenbsort100-syntheticbench1-malardalenbsort100.csv', sep=' ')
pv4

pv4 = pd.read_csv('report/data/cycles-3core-syntheticbench1.csv', sep=' ')
pv4
