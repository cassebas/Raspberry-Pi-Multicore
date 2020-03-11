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

df0 = pd.read_csv('output/20200226-array_access_random-4core.csv')
df0 = df0.loc[df0['core'] == 2]
df0.boxplot(column='cycles') 
df0.describe()

df = pd.read_csv('output/20200122-malardalen_bsort100_1core-clearcache.csv')
df.boxplot(column='cycles') 
df.describe()
