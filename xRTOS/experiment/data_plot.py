import pandas as pd
import matplotlib.pyplot as plt

# 1 core - no corunners
cycles_task = pd.read_csv('array_access_linear_1cores_preemptive.csv',
                          sep=' ')
print('Linear array access - 1 task, median = {}'.format(cycles_task['cycles'].median()))
print(cycles_task['cycles'].describe().apply(lambda x: format(x, 'f')))

cycles_task.boxplot(column='cycles')
plt.savefig('array_access_linear_1cores_preemptive.png')


# 2 cores - 1 corunner
cycles_task = pd.read_csv('array_access_linear_2cores_preemptive.csv',
                          sep=' ')
print('Linear array access - 2 cores, median = {}'.format(cycles_task['cycles'].median()))
print(cycles_task['cycles'].describe().apply(lambda x: format(x, 'f')))

cycles_task.boxplot(column='cycles')
plt.savefig('array_access_linear_2cores_preemptive.png')


# 4 cores - 3 corunners
cycles_task = pd.read_csv('array_access_linear_4cores_preemptive.csv',
                          sep=' ')
print('Linear array access - 4 cores, median = {}'.format(cycles_task['cycles'].median()))
print(cycles_task['cycles'].describe().apply(lambda x: format(x, 'f')))

cycles_task.boxplot(column='cycles')
plt.savefig('array_access_linear_4cores_preemptive.png')



# Mälardalen bsort100: 2 cores - 1 corunner
cycles_task = pd.read_csv('malardalen_bsort100_2cores_preemptive-2.csv',
                          sep=' ')
print('Mälardalen bsort100 - 2 cores, median = {}'.format(cycles_task['cycles'].median()))
print(cycles_task['cycles'].describe().apply(lambda x: format(x, 'f')))

cycles_task.boxplot(column='cycles')
plt.savefig('malardalen_bsort100_2cores_preemptive-2.png')



# Mälardalen bsort100: 4 cores - 3 corunners
cycles_task = pd.read_csv('malardalen_bsort100_4cores_preemptive.csv',
                          sep=' ')
print('Mälardalen bsort100 - 4 cores, median = {}'.format(cycles_task['cycles'].median()))
print(cycles_task['cycles'].describe().apply(lambda x: format(x, 'f')))

cycles_task.boxplot(column='cycles')
plt.savefig('malardalen_bsort100_4cores_preemptive.png')
